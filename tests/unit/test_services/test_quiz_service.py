"""
Unit tests for QuizService.

Tests quiz session creation, question generation, answer validation,
and quiz completion.
"""

import pytest

from app.services.quiz_service import (
    QuizService,
    QuizMode,
    QuizDifficulty,
    QuizSession,
)
from app.services.content_service import ContentType


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuizService:
    """Tests for QuizService class."""

    async def test_create_quiz_session(self, quiz_service: QuizService):
        """Test creating a quiz session."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=5,
        )

        assert session is not None
        assert session.mode == QuizMode.MULTIPLE_CHOICE
        assert session.difficulty == QuizDifficulty.EASY
        assert session.content_type == ContentType.HIRAGANA
        assert len(session.questions) <= 5

    async def test_create_quiz_with_learned_characters(self, quiz_service: QuizService):
        """Test creating quiz with learned character IDs."""
        learned_ids = ["hira_001", "hira_002", "hira_003"]

        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.MEDIUM,
            content_type=ContentType.HIRAGANA,
            question_count=3,
            learned_character_ids=learned_ids,
        )

        assert session is not None
        # Should prioritize learned characters
        assert len(session.questions) > 0

    async def test_quiz_session_initialization(self, quiz_service: QuizService):
        """Test quiz session is properly initialized."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.RECOGNITION,
            difficulty=QuizDifficulty.HARD,
            content_type=ContentType.KATAKANA,
            question_count=10,
        )

        assert session.current_question_index == 0
        assert session.correct_answers == 0
        assert session.total_attempts == 0
        assert session.start_time is not None
        assert session.answers_history == []

    async def test_multiple_choice_question_format(self, quiz_service: QuizService):
        """Test that multiple choice questions have proper format."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        if session and session.questions:
            question = session.questions[0]
            assert question.mode == QuizMode.MULTIPLE_CHOICE
            assert question.options is not None
            assert len(question.options) >= 3  # Easy mode has 3 options
            assert question.correct_answer in question.options

    async def test_typing_question_format(self, quiz_service: QuizService):
        """Test that typing questions have proper format."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.MEDIUM,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        if session and session.questions:
            question = session.questions[0]
            assert question.mode == QuizMode.TYPING
            assert question.options is None  # Typing has no options
            assert question.correct_answer is not None

    async def test_recognition_question_format(self, quiz_service: QuizService):
        """Test that recognition questions have proper format."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.RECOGNITION,
            difficulty=QuizDifficulty.HARD,
            content_type=ContentType.KATAKANA,
            question_count=1,
        )

        if session and session.questions:
            question = session.questions[0]
            assert question.mode == QuizMode.RECOGNITION
            assert question.options is not None
            assert question.correct_answer in question.options

    async def test_get_current_question(self, quiz_service: QuizService):
        """Test getting the current question."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=5,
        )

        current = await quiz_service.get_current_question(session)

        assert current is not None
        assert current == session.questions[0]

    async def test_get_current_question_at_end(self, quiz_service: QuizService):
        """Test getting current question when quiz is complete."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.MEDIUM,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        # Move to end
        session.current_question_index = len(session.questions)

        current = await quiz_service.get_current_question(session)
        assert current is None

    async def test_submit_correct_answer(self, quiz_service: QuizService):
        """Test submitting a correct answer."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        question = session.questions[0]
        correct_answer = question.correct_answer

        is_correct, feedback, explanation = await quiz_service.submit_answer(
            session, correct_answer
        )

        assert is_correct is True
        assert session.correct_answers == 1
        assert session.total_attempts == 1
        assert len(session.answers_history) == 1

    async def test_submit_incorrect_answer(self, quiz_service: QuizService):
        """Test submitting an incorrect answer."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        is_correct, feedback, explanation = await quiz_service.submit_answer(
            session, "wrong_answer"
        )

        assert is_correct is False
        assert session.correct_answers == 0
        assert session.total_attempts == 1
        assert explanation is not None  # Should provide explanation

    async def test_submit_answer_case_insensitive(self, quiz_service: QuizService):
        """Test that answer submission is case-insensitive."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        question = session.questions[0]
        correct_answer = question.correct_answer.upper()  # Change case

        is_correct, _, _ = await quiz_service.submit_answer(session, correct_answer)

        assert is_correct is True

    async def test_advance_to_next_question(self, quiz_service: QuizService):
        """Test advancing to the next question."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=3,
        )

        initial_index = session.current_question_index
        has_more = await quiz_service.advance_to_next_question(session)

        assert has_more is True
        assert session.current_question_index == initial_index + 1

    async def test_advance_at_last_question(self, quiz_service: QuizService):
        """Test advancing when at the last question."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.MEDIUM,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        # Move to last question
        session.current_question_index = len(session.questions) - 1

        has_more = await quiz_service.advance_to_next_question(session)

        assert has_more is False

    async def test_complete_quiz(self, quiz_service: QuizService):
        """Test completing a quiz."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=2,
        )

        # Answer questions
        session.correct_answers = 1
        session.total_attempts = 2

        summary = await quiz_service.complete_quiz(session)

        assert "quiz_mode" in summary
        assert "accuracy" in summary
        assert "total_questions" in summary
        assert "performance" in summary
        assert summary["accuracy"] == 50.0  # 1/2 = 50%

    async def test_quiz_performance_tiers(self, quiz_service: QuizService):
        """Test that performance tiers are assigned correctly."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.TYPING,
            difficulty=QuizDifficulty.MEDIUM,
            content_type=ContentType.HIRAGANA,
            question_count=10,
        )

        # Test excellent (90%+)
        session.correct_answers = 9
        session.total_attempts = 10
        summary = await quiz_service.complete_quiz(session)
        assert "Excellent" in summary["performance"]

        # Test great (75-89%)
        session.correct_answers = 8
        summary = await quiz_service.complete_quiz(session)
        assert "Great" in summary["performance"]

        # Test good (60-74%)
        session.correct_answers = 7
        summary = await quiz_service.complete_quiz(session)
        assert "Good" in summary["performance"]

        # Test keep practicing (<60%)
        session.correct_answers = 5
        summary = await quiz_service.complete_quiz(session)
        assert "Keep Practicing" in summary["performance"]

    async def test_get_hint(self, quiz_service: QuizService):
        """Test getting a hint for the current question."""
        session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,  # Easy mode has hints
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        hint = await quiz_service.get_hint(session)

        # Hint may or may not exist depending on question
        if hint:
            assert isinstance(hint, str)
            assert len(hint) > 0

    async def test_difficulty_affects_option_count(self, quiz_service: QuizService):
        """Test that difficulty affects the number of options."""
        # Easy mode
        easy_session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.EASY,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        # Hard mode
        hard_session = await quiz_service.create_quiz_session(
            mode=QuizMode.MULTIPLE_CHOICE,
            difficulty=QuizDifficulty.HARD,
            content_type=ContentType.HIRAGANA,
            question_count=1,
        )

        if easy_session and easy_session.questions:
            easy_options = len(easy_session.questions[0].options or [])
            # Easy should have 3 options (2 wrong + 1 correct)
            assert easy_options == 3

        if hard_session and hard_session.questions:
            hard_options = len(hard_session.questions[0].options or [])
            # Hard should have 4 options (3 wrong + 1 correct)
            assert hard_options == 4
