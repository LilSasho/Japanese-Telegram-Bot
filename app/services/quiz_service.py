"""
Quiz service for the Japanese Learning Telegram Bot.

This module handles quiz generation, question creation, and answer validation
for three quiz modes: multiple choice, typing practice, and character recognition.
"""

import random
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

from app.services.content_service import ContentService, CharacterData, ContentType


class QuizMode(Enum):
    """Quiz mode types."""

    MULTIPLE_CHOICE = "multiple_choice"
    TYPING = "typing"
    RECOGNITION = "recognition"


class QuizDifficulty(Enum):
    """Quiz difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class QuizQuestion:
    """Represents a single quiz question."""

    question_id: str
    mode: QuizMode
    prompt: str
    correct_answer: str
    options: Optional[List[str]] = None  # For multiple choice
    character_data: Optional[CharacterData] = None
    hints: Optional[List[str]] = None


@dataclass
class QuizSession:
    """Tracks an active quiz session."""

    quiz_id: str
    mode: QuizMode
    difficulty: QuizDifficulty
    content_type: ContentType
    questions: List[QuizQuestion]
    current_question_index: int = 0
    correct_answers: int = 0
    total_attempts: int = 0
    start_time: datetime = None
    answers_history: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)
        if self.answers_history is None:
            self.answers_history = []


class QuizService:
    """Service for managing quizzes and questions."""

    def __init__(self, content_service: ContentService):
        """
        Initialize the quiz service.

        Args:
            content_service: ContentService instance for accessing learning content
        """
        self.content_service = content_service

    async def create_quiz_session(
        self,
        mode: QuizMode,
        difficulty: QuizDifficulty,
        content_type: ContentType,
        question_count: int = 10,
        learned_character_ids: Optional[List[str]] = None,
    ) -> Optional[QuizSession]:
        """
        Create a new quiz session.

        Args:
            mode: Quiz mode (multiple choice, typing, recognition)
            difficulty: Quiz difficulty level
            content_type: Type of content to quiz on
            question_count: Number of questions to generate
            learned_character_ids: IDs of characters the user has learned

        Returns:
            QuizSession object or None if insufficient content
        """
        # Get characters for the quiz
        characters = await self._get_quiz_characters(
            content_type, question_count, learned_character_ids
        )

        if not characters:
            return None

        # Generate questions based on mode
        questions = await self._generate_questions(
            characters, mode, difficulty, content_type
        )

        if not questions:
            return None

        quiz_id = f"quiz_{mode.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return QuizSession(
            quiz_id=quiz_id,
            mode=mode,
            difficulty=difficulty,
            content_type=content_type,
            questions=questions,
        )

    async def _get_quiz_characters(
        self,
        content_type: ContentType,
        count: int,
        learned_character_ids: Optional[List[str]],
    ) -> List[CharacterData]:
        """
        Get characters for the quiz.

        Args:
            content_type: Type of content
            count: Number of characters needed
            learned_character_ids: IDs of learned characters to focus on

        Returns:
            List of CharacterData objects
        """
        if learned_character_ids:
            # Get learned characters for review
            characters = []
            for char_id in learned_character_ids:
                char = await self.content_service.get_character_by_id(char_id)
                if char and char.content_type == content_type:
                    characters.append(char)

            # If not enough learned characters, add some new ones
            if len(characters) < count:
                suggested = await self.content_service.get_next_characters_to_learn(
                    set(learned_character_ids), content_type, count - len(characters)
                )
                characters.extend(suggested)
        else:
            # Get beginner characters (difficulty 1)
            characters = await self.content_service.get_characters_by_difficulty(
                difficulty=1, content_type=content_type, limit=count
            )

        # Shuffle for randomness
        random.shuffle(characters)
        return characters[:count]

    async def _generate_questions(
        self,
        characters: List[CharacterData],
        mode: QuizMode,
        difficulty: QuizDifficulty,
        content_type: ContentType,
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions based on characters and mode.

        Args:
            characters: List of characters to quiz on
            mode: Quiz mode
            difficulty: Quiz difficulty
            content_type: Type of content

        Returns:
            List of QuizQuestion objects
        """
        questions = []

        for idx, character in enumerate(characters):
            if mode == QuizMode.MULTIPLE_CHOICE:
                question = await self._create_multiple_choice_question(
                    character, idx, difficulty, content_type
                )
            elif mode == QuizMode.TYPING:
                question = await self._create_typing_question(
                    character, idx, difficulty
                )
            elif mode == QuizMode.RECOGNITION:
                question = await self._create_recognition_question(
                    character, idx, difficulty, content_type
                )
            else:
                continue

            if question:
                questions.append(question)

        return questions

    async def _create_multiple_choice_question(
        self,
        character: CharacterData,
        question_num: int,
        difficulty: QuizDifficulty,
        content_type: ContentType,
    ) -> QuizQuestion:
        """Create a multiple choice question."""
        # Get wrong answer options from similar characters
        all_chars = await self.content_service.get_characters_by_difficulty(
            difficulty=character.difficulty, content_type=content_type
        )

        # Filter out the correct answer and get wrong options
        wrong_options = [
            char.romaji
            for char in all_chars
            if char.id != character.id and char.romaji != character.romaji
        ]

        # Determine number of options based on difficulty
        num_wrong = 2 if difficulty == QuizDifficulty.EASY else 3

        # Randomly select wrong answers
        if len(wrong_options) >= num_wrong:
            selected_wrong = random.sample(wrong_options, num_wrong)
        else:
            selected_wrong = wrong_options

        # Create options list with correct answer
        options = selected_wrong + [character.romaji]
        random.shuffle(options)

        prompt = f"What is the romaji reading of {character.character}?"

        # Add hints for easy mode
        hints = None
        if difficulty == QuizDifficulty.EASY and character.mnemonics:
            hints = [character.mnemonics]

        return QuizQuestion(
            question_id=f"mc_{question_num}",
            mode=QuizMode.MULTIPLE_CHOICE,
            prompt=prompt,
            correct_answer=character.romaji,
            options=options,
            character_data=character,
            hints=hints,
        )

    async def _create_typing_question(
        self, character: CharacterData, question_num: int, difficulty: QuizDifficulty
    ) -> QuizQuestion:
        """Create a typing question."""
        prompt = f"Type the romaji reading of: {character.character}"

        # Add hints based on difficulty
        hints = []
        if difficulty == QuizDifficulty.EASY:
            if character.mnemonics:
                hints.append(character.mnemonics)
            hints.append(f"First letter: {character.romaji[0]}")
        elif difficulty == QuizDifficulty.MEDIUM:
            if character.mnemonics:
                hints.append(character.mnemonics)

        return QuizQuestion(
            question_id=f"type_{question_num}",
            mode=QuizMode.TYPING,
            prompt=prompt,
            correct_answer=character.romaji.lower(),
            character_data=character,
            hints=hints if hints else None,
        )

    async def _create_recognition_question(
        self,
        character: CharacterData,
        question_num: int,
        difficulty: QuizDifficulty,
        content_type: ContentType,
    ) -> QuizQuestion:
        """Create a character recognition question (reverse: romaji -> character)."""
        # Get similar characters for wrong options
        all_chars = await self.content_service.get_characters_by_difficulty(
            difficulty=character.difficulty, content_type=content_type
        )

        # Filter out the correct answer
        wrong_options = [
            char.character
            for char in all_chars
            if char.id != character.id and char.character != character.character
        ]

        # Determine number of options based on difficulty
        num_wrong = 2 if difficulty == QuizDifficulty.EASY else 3

        # Randomly select wrong answers
        if len(wrong_options) >= num_wrong:
            selected_wrong = random.sample(wrong_options, num_wrong)
        else:
            selected_wrong = wrong_options

        # Create options list with correct answer
        options = selected_wrong + [character.character]
        random.shuffle(options)

        prompt = f"Which character represents the sound '{character.romaji}'?"

        hints = None
        if difficulty == QuizDifficulty.EASY and character.mnemonics:
            hints = [f"Remember: {character.mnemonics}"]

        return QuizQuestion(
            question_id=f"recog_{question_num}",
            mode=QuizMode.RECOGNITION,
            prompt=prompt,
            correct_answer=character.character,
            options=options,
            character_data=character,
            hints=hints,
        )

    async def get_current_question(
        self, session: QuizSession
    ) -> Optional[QuizQuestion]:
        """
        Get the current question in the quiz session.

        Args:
            session: Active quiz session

        Returns:
            Current QuizQuestion or None if quiz is complete
        """
        if session.current_question_index >= len(session.questions):
            return None

        return session.questions[session.current_question_index]

    async def submit_answer(
        self, session: QuizSession, user_answer: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Submit an answer for the current question.

        Args:
            session: Active quiz session
            user_answer: User's answer

        Returns:
            Tuple of (is_correct, feedback_message, detailed_explanation)
        """
        current_question = await self.get_current_question(session)

        if not current_question:
            return False, "Quiz session has ended.", None

        session.total_attempts += 1

        # Normalize answers for comparison
        user_answer_normalized = user_answer.strip().lower()
        correct_answer_normalized = current_question.correct_answer.strip().lower()

        is_correct = user_answer_normalized == correct_answer_normalized

        # Record answer in history
        session.answers_history.append(
            {
                "question_id": current_question.question_id,
                "user_answer": user_answer,
                "correct_answer": current_question.correct_answer,
                "is_correct": is_correct,
                "timestamp": datetime.now(timezone.utc),
            }
        )

        # Generate feedback
        if is_correct:
            session.correct_answers += 1
            feedback = f"✅ Correct!"

            # Add context
            if current_question.character_data:
                char = current_question.character_data
                if char.meaning:
                    feedback += f" {char.character} ({char.romaji}) - {char.meaning}"
                else:
                    feedback += f" {char.character} = {char.romaji}"

            explanation = None

        else:
            feedback = f"❌ Not quite. The correct answer is: {current_question.correct_answer}"

            # Build detailed explanation
            explanation = None
            if current_question.character_data:
                char = current_question.character_data
                explanation_parts = [f"📝 {char.character} = {char.romaji}"]

                if char.meaning:
                    explanation_parts.append(f"Meaning: {char.meaning}")

                if char.mnemonics:
                    explanation_parts.append(f"💡 Tip: {char.mnemonics}")

                if char.examples:
                    example = char.examples[0]
                    explanation_parts.append(
                        f"Example: {example.word} ({example.romaji}) - {example.meaning}"
                    )

                explanation = "\n".join(explanation_parts)

        return is_correct, feedback, explanation

    async def advance_to_next_question(self, session: QuizSession) -> bool:
        """
        Advance to the next question.

        Args:
            session: Active quiz session

        Returns:
            True if there are more questions, False if quiz is complete
        """
        session.current_question_index += 1
        return session.current_question_index < len(session.questions)

    async def complete_quiz(self, session: QuizSession) -> Dict[str, Any]:
        """
        Complete the quiz and return summary statistics.

        Args:
            session: Completed quiz session

        Returns:
            Quiz completion summary
        """
        end_time = datetime.now(timezone.utc)
        duration = end_time - session.start_time
        accuracy = (session.correct_answers / max(session.total_attempts, 1)) * 100

        # Calculate performance tier
        if accuracy >= 90:
            performance = "🌟 Excellent"
        elif accuracy >= 75:
            performance = "⭐ Great"
        elif accuracy >= 60:
            performance = "👍 Good"
        else:
            performance = "📚 Keep Practicing"

        summary = {
            "quiz_mode": session.mode.value,
            "content_type": session.content_type.value,
            "difficulty": session.difficulty.value,
            "total_questions": len(session.questions),
            "correct_answers": session.correct_answers,
            "total_attempts": session.total_attempts,
            "accuracy": round(accuracy, 1),
            "duration_seconds": int(duration.total_seconds()),
            "performance": performance,
            "answered_incorrectly": [
                ans for ans in session.answers_history if not ans["is_correct"]
            ],
        }

        return summary

    async def get_hint(self, session: QuizSession) -> Optional[str]:
        """
        Get a hint for the current question.

        Args:
            session: Active quiz session

        Returns:
            Hint string or None if no hints available
        """
        current_question = await self.get_current_question(session)

        if not current_question or not current_question.hints:
            return None

        # Return a random hint from available hints
        return random.choice(current_question.hints)
