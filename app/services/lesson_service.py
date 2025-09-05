"""
Lesson service for the Japanese Learning Telegram Bot.

This module handles lesson creation, content delivery, and learning progression
for the bot's educational features.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from app.models.user import User, LearningLevel
from app.models.lesson import Lesson, LessonType, LessonDifficulty
from app.models.progress import UserProgress


class ContentType(Enum):
    """Types of learning content."""

    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    KANJI = "kanji"
    VOCABULARY = "vocabulary"


@dataclass
class Character:
    """Represents a Japanese character for learning."""

    character: str
    romaji: str
    meaning: Optional[str] = None
    stroke_count: Optional[int] = None
    frequency: Optional[int] = None
    mnemonics: Optional[str] = None
    audio_file: Optional[str] = None


@dataclass
class LessonContent:
    """Contains the content for a lesson."""

    lesson_id: str
    content_type: ContentType
    difficulty: LessonDifficulty
    characters: List[Character]
    title: str
    description: str
    learning_tips: List[str]
    cultural_notes: Optional[str] = None


@dataclass
class LessonProgress:
    """Tracks progress within a lesson."""

    current_character_index: int = 0
    correct_answers: int = 0
    total_attempts: int = 0
    start_time: datetime = None
    mistakes: List[str] = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)
        if self.mistakes is None:
            self.mistakes = []


class LessonService:
    """Service for managing lessons and learning content."""

    def __init__(self):
        self._content_cache: Dict[ContentType, Dict] = {}
        self._data_dir = Path("data/content")

    async def initialize(self):
        """Initialize the lesson service and load content."""
        await self._load_content()

    async def _load_content(self):
        """Load learning content from JSON files."""
        content_files = {
            ContentType.HIRAGANA: "hiragana/basic.json",
            ContentType.KATAKANA: "katakana/basic.json",
            ContentType.KANJI: "kanji/basic.json",
            ContentType.VOCABULARY: "vocabulary/basic.json",
        }

        for content_type, file_path in content_files.items():
            full_path = self._data_dir / file_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        self._content_cache[content_type] = content
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    # Create minimal fallback content
                    self._content_cache[content_type] = self._get_fallback_content(
                        content_type
                    )
            else:
                # Create fallback content if file doesn't exist
                self._content_cache[content_type] = self._get_fallback_content(
                    content_type
                )

    def _get_fallback_content(self, content_type: ContentType) -> Dict:
        """Create fallback content when files are missing."""
        if content_type == ContentType.HIRAGANA:
            return {
                "name": "Basic Hiragana",
                "description": "Learn the basic hiragana characters",
                "characters": [
                    {"character": "あ", "romaji": "a", "meaning": "vowel sound 'ah'"},
                    {"character": "か", "romaji": "ka", "meaning": "ka sound"},
                    {"character": "さ", "romaji": "sa", "meaning": "sa sound"},
                    {"character": "た", "romaji": "ta", "meaning": "ta sound"},
                    {"character": "な", "romaji": "na", "meaning": "na sound"},
                ],
            }
        elif content_type == ContentType.KATAKANA:
            return {
                "name": "Basic Katakana",
                "description": "Learn the basic katakana characters",
                "characters": [
                    {"character": "ア", "romaji": "a", "meaning": "vowel sound 'ah'"},
                    {"character": "カ", "romaji": "ka", "meaning": "ka sound"},
                    {"character": "サ", "romaji": "sa", "meaning": "sa sound"},
                ],
            }
        else:
            return {
                "name": f"Basic {content_type.value.title()}",
                "description": f"Learn basic {content_type.value}",
                "characters": [],
            }

    async def get_available_lessons(self, user: User) -> List[Dict[str, Any]]:
        """
        Get list of available lessons for a user based on their progress.

        Args:
            user: User object

        Returns:
            List of available lesson information
        """
        lessons = []

        # Hiragana is always available
        if self._content_cache.get(ContentType.HIRAGANA):
            lessons.append(
                {
                    "type": ContentType.HIRAGANA,
                    "title": "🌸 Hiragana",
                    "description": "Basic Japanese phonetic script",
                    "unlocked": True,
                    "progress": await self._get_content_progress(
                        user, ContentType.HIRAGANA
                    ),
                }
            )

        # Check other content based on user progress
        if user.katakana_unlocked and self._content_cache.get(ContentType.KATAKANA):
            lessons.append(
                {
                    "type": ContentType.KATAKANA,
                    "title": "🌺 Katakana",
                    "description": "Japanese script for foreign words",
                    "unlocked": True,
                    "progress": await self._get_content_progress(
                        user, ContentType.KATAKANA
                    ),
                }
            )

        if user.kanji_unlocked and self._content_cache.get(ContentType.KANJI):
            lessons.append(
                {
                    "type": ContentType.KANJI,
                    "title": "🏯 Basic Kanji",
                    "description": "Essential Chinese characters used in Japanese",
                    "unlocked": True,
                    "progress": await self._get_content_progress(
                        user, ContentType.KANJI
                    ),
                }
            )

        if user.vocabulary_unlocked and self._content_cache.get(ContentType.VOCABULARY):
            lessons.append(
                {
                    "type": ContentType.VOCABULARY,
                    "title": "💬 Vocabulary",
                    "description": "Common Japanese words and phrases",
                    "unlocked": True,
                    "progress": await self._get_content_progress(
                        user, ContentType.VOCABULARY
                    ),
                }
            )

        return lessons

    async def _get_content_progress(
        self, user: User, content_type: ContentType
    ) -> Dict[str, Any]:
        """Get user's progress for specific content type."""
        # This would query the database for user progress
        # For now, return mock progress
        return {
            "characters_learned": 0,
            "total_characters": len(
                self._content_cache.get(content_type, {}).get("characters", [])
            ),
            "accuracy": 0.0,
            "last_lesson": None,
        }

    async def create_lesson(
        self, user: User, content_type: ContentType, difficulty: LessonDifficulty
    ) -> Optional[LessonContent]:
        """
        Create a lesson for the user based on their progress and preferences.

        Args:
            user: User object
            content_type: Type of content to learn
            difficulty: Lesson difficulty

        Returns:
            LessonContent object or None if no content available
        """
        content = self._content_cache.get(content_type)
        if not content:
            return None

        # Determine lesson size based on difficulty and user preferences
        lesson_size = self._get_lesson_size(difficulty, user)

        # Get characters for this lesson based on user progress
        characters = await self._select_lesson_characters(
            user, content_type, lesson_size
        )

        if not characters:
            return None

        lesson_id = f"{content_type.value}_{difficulty.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return LessonContent(
            lesson_id=lesson_id,
            content_type=content_type,
            difficulty=difficulty,
            characters=characters,
            title=content.get("name", f"{content_type.value.title()} Lesson"),
            description=content.get(
                "description", f"Learn {content_type.value} characters"
            ),
            learning_tips=content.get(
                "tips",
                [
                    "Take your time to memorize each character",
                    "Practice writing the characters",
                    "Use mnemonics to remember better",
                ],
            ),
            cultural_notes=content.get("cultural_notes"),
        )

    def _get_lesson_size(self, difficulty: LessonDifficulty, user: User) -> int:
        """Determine lesson size based on difficulty and user preferences."""
        base_size = user.lesson_size

        if difficulty == LessonDifficulty.EASY:
            return max(3, base_size // 2)
        elif difficulty == LessonDifficulty.MEDIUM:
            return base_size
        elif difficulty == LessonDifficulty.HARD:
            return min(10, base_size * 2)
        else:  # CHALLENGE
            return min(15, base_size * 3)

    async def _select_lesson_characters(
        self, user: User, content_type: ContentType, count: int
    ) -> List[Character]:
        """
        Select characters for a lesson based on spaced repetition algorithm.

        Args:
            user: User object
            content_type: Type of content
            count: Number of characters to select

        Returns:
            List of Character objects
        """
        content = self._content_cache.get(content_type, {})
        all_characters = content.get("characters", [])

        if not all_characters:
            return []

        # Convert to Character objects
        characters = []
        for char_data in all_characters:
            char = Character(
                character=char_data.get("character", ""),
                romaji=char_data.get("romaji", ""),
                meaning=char_data.get("meaning"),
                stroke_count=char_data.get("stroke_count"),
                frequency=char_data.get("frequency"),
                mnemonics=char_data.get("mnemonics"),
                audio_file=char_data.get("audio_file"),
            )
            characters.append(char)

        # For now, randomly select characters
        # TODO: Implement spaced repetition algorithm
        selected = random.sample(characters, min(count, len(characters)))
        return selected

    async def get_next_character_in_lesson(
        self, lesson: LessonContent, progress: LessonProgress
    ) -> Optional[Character]:
        """
        Get the next character in the lesson based on current progress.

        Args:
            lesson: LessonContent object
            progress: Current lesson progress

        Returns:
            Next Character object or None if lesson complete
        """
        if progress.current_character_index >= len(lesson.characters):
            return None

        return lesson.characters[progress.current_character_index]

    async def record_answer(
        self,
        lesson: LessonContent,
        progress: LessonProgress,
        character: Character,
        user_answer: str,
        correct_answer: str,
    ) -> Tuple[bool, str]:
        """
        Record a user's answer and provide feedback.

        Args:
            lesson: LessonContent object
            progress: Current lesson progress
            character: Character being answered
            user_answer: User's answer
            correct_answer: Correct answer

        Returns:
            Tuple of (is_correct, feedback_message)
        """
        progress.total_attempts += 1
        is_correct = user_answer.lower().strip() == correct_answer.lower().strip()

        if is_correct:
            progress.correct_answers += 1
            feedback = (
                f"✅ Correct! {character.character} is pronounced '{character.romaji}'"
            )
            if character.meaning:
                feedback += f" ({character.meaning})"
        else:
            progress.mistakes.append(character.character)
            feedback = f"❌ Not quite. {character.character} is pronounced '{character.romaji}', not '{user_answer}'"
            if character.meaning:
                feedback += f" ({character.meaning})"
            if character.mnemonics:
                feedback += f"\n💡 Tip: {character.mnemonics}"

        return is_correct, feedback

    async def advance_lesson_progress(self, progress: LessonProgress) -> bool:
        """
        Advance to the next character in the lesson.

        Args:
            progress: Current lesson progress

        Returns:
            True if there are more characters, False if lesson is complete
        """
        progress.current_character_index += 1
        return (
            progress.current_character_index
            < len(progress.mistakes) + progress.correct_answers
        )

    async def complete_lesson(
        self, user: User, lesson: LessonContent, progress: LessonProgress
    ) -> Dict[str, Any]:
        """
        Complete a lesson and return summary statistics.

        Args:
            user: User object
            lesson: LessonContent object
            progress: Final lesson progress

        Returns:
            Lesson completion summary
        """
        end_time = datetime.now(timezone.utc)
        duration = end_time - progress.start_time
        accuracy = progress.correct_answers / max(progress.total_attempts, 1) * 100

        # Update user progress (this would save to database)
        user.total_lessons_completed += 1
        user.last_lesson_at = end_time

        summary = {
            "lesson_type": lesson.content_type.value,
            "characters_practiced": len(lesson.characters),
            "correct_answers": progress.correct_answers,
            "total_attempts": progress.total_attempts,
            "accuracy": round(accuracy, 1),
            "duration_minutes": round(duration.total_seconds() / 60, 1),
            "mistakes": progress.mistakes,
            "achievement_unlocked": None,  # TODO: Check for achievements
        }

        return summary
