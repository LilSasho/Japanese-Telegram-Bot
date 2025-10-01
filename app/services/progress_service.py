"""
Progress tracking service for the Japanese Learning Telegram Bot.

This module provides comprehensive progress tracking functionality including:
- User progress management with SM-2 spaced repetition integration
- Review scheduling and due item retrieval
- Performance analytics and statistics
- Learning session management
- Integration with ContentService for personalized learning paths
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set, Dict, Any, Tuple
from decimal import Decimal

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import (
    UserProgress,
    LearningSession,
    ContentType,
    DifficultyLevel,
)
from app.utils.spaced_repetition import (
    SpacedRepetitionSM2,
    QualityRating,
)
from app.services.content_service import ContentService, CharacterData


# Configure logging
logger = logging.getLogger(__name__)


class ProgressService:
    """Service for managing user learning progress and spaced repetition."""

    def __init__(
        self,
        db_session: AsyncSession,
        content_service: Optional[ContentService] = None,
    ):
        """
        Initialize the progress service.

        Args:
            db_session: SQLAlchemy async database session
            content_service: Content service for character data (optional)
        """
        self.db = db_session
        self.content_service = content_service
        self.sm2 = SpacedRepetitionSM2()

    async def get_or_create_progress(
        self, user_id: int, content_type: ContentType, content_id: str
    ) -> UserProgress:
        """
        Get existing progress record or create a new one.

        Args:
            user_id: User's Telegram ID
            content_type: Type of content (hiragana, katakana, etc.)
            content_id: Unique content identifier

        Returns:
            UserProgress record
        """
        # Try to find existing progress
        stmt = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.content_type == content_type,
                UserProgress.content_id == content_id,
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress:
            return progress

        # Create new progress record
        progress = UserProgress(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            easiness_factor=Decimal("2.5"),  # Default SM-2 easiness
            repetition_count=0,
            interval=1,
            needs_review=True,
            next_review_at=datetime.now(timezone.utc),
        )

        self.db.add(progress)
        await self.db.flush()

        logger.info(
            f"Created new progress record: user={user_id}, "
            f"content={content_type.value}:{content_id}"
        )

        return progress

    async def record_review(
        self,
        user_id: int,
        content_type: ContentType,
        content_id: str,
        quality_rating: int,
        response_time_ms: Optional[int] = None,
    ) -> UserProgress:
        """
        Record a review attempt and update spaced repetition parameters.

        Args:
            user_id: User's Telegram ID
            content_type: Type of content
            content_id: Content identifier
            quality_rating: Quality rating (0-5) from QualityRating enum
            response_time_ms: Response time in milliseconds

        Returns:
            Updated UserProgress record
        """
        # Get or create progress record
        progress = await self.get_or_create_progress(user_id, content_type, content_id)

        # Calculate new SM-2 parameters
        review_result = self.sm2.calculate_next_review(
            quality=quality_rating,
            current_easiness=progress.easiness_factor,
            current_repetitions=progress.repetition_count,
            current_interval=progress.interval,
            last_review_date=datetime.now(timezone.utc),
        )

        # Update progress with SM-2 results
        progress.easiness_factor = review_result.easiness_factor
        progress.repetition_count = review_result.repetition_count
        progress.interval = review_result.interval_days
        progress.next_review_at = review_result.next_review_date

        # Update attempt counters
        progress.total_attempts += 1
        is_correct = quality_rating >= QualityRating.CORRECT_DIFFICULT
        if is_correct:
            progress.correct_attempts += 1

        # Update response time (exponential moving average)
        if response_time_ms is not None:
            if progress.average_response_time_ms is None:
                progress.average_response_time_ms = response_time_ms
            else:
                alpha = 0.3  # Weight for new measurement
                progress.average_response_time_ms = int(
                    alpha * response_time_ms
                    + (1 - alpha) * progress.average_response_time_ms
                )

        # Update learning status flags
        self._update_learning_status(progress)

        # Update timestamps
        progress.last_reviewed_at = datetime.now(timezone.utc)
        progress.updated_at = datetime.now(timezone.utc)

        # Determine if needs review based on repetition count
        progress.needs_review = progress.repetition_count < 5  # Master after 5 reps

        await self.db.flush()

        logger.info(
            f"Recorded review: user={user_id}, content={content_id}, "
            f"quality={quality_rating}, interval={review_result.interval_days}d"
        )

        return progress

    def _update_learning_status(self, progress: UserProgress) -> None:
        """
        Update learning status flags based on performance.

        Args:
            progress: UserProgress record to update
        """
        accuracy = progress.accuracy_percentage

        # Update difficulty level
        if accuracy >= 95:
            progress.current_difficulty = DifficultyLevel.VERY_EASY
        elif accuracy >= 85:
            progress.current_difficulty = DifficultyLevel.EASY
        elif accuracy >= 70:
            progress.current_difficulty = DifficultyLevel.NORMAL
        elif accuracy >= 50:
            progress.current_difficulty = DifficultyLevel.HARD
        else:
            progress.current_difficulty = DifficultyLevel.VERY_HARD

        # Mark as learned: 80%+ accuracy with 3+ attempts
        if progress.total_attempts >= 3 and accuracy >= 80:
            progress.is_learned = True

        # Mark as mastered: 95%+ accuracy with 5+ attempts
        if progress.total_attempts >= 5 and accuracy >= 95:
            progress.is_mastered = True

    async def get_due_reviews(
        self,
        user_id: int,
        content_type: Optional[ContentType] = None,
        limit: Optional[int] = None,
    ) -> List[UserProgress]:
        """
        Get items that are due for review.

        Args:
            user_id: User's Telegram ID
            content_type: Filter by content type (optional)
            limit: Maximum number of items to return

        Returns:
            List of UserProgress records due for review
        """
        now = datetime.now(timezone.utc)

        # Build query
        conditions = [
            UserProgress.user_id == user_id,
            UserProgress.needs_review.is_(True),
            UserProgress.next_review_at <= now,
        ]

        if content_type:
            conditions.append(UserProgress.content_type == content_type)

        stmt = (
            select(UserProgress)
            .where(and_(*conditions))
            .order_by(UserProgress.next_review_at.asc())  # Oldest reviews first
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_review_count(
        self, user_id: int, content_type: Optional[ContentType] = None
    ) -> int:
        """
        Get count of items due for review.

        Args:
            user_id: User's Telegram ID
            content_type: Filter by content type (optional)

        Returns:
            Number of items due for review
        """
        now = datetime.now(timezone.utc)

        conditions = [
            UserProgress.user_id == user_id,
            UserProgress.needs_review.is_(True),
            UserProgress.next_review_at <= now,
        ]

        if content_type:
            conditions.append(UserProgress.content_type == content_type)

        stmt = select(func.count()).select_from(UserProgress).where(and_(*conditions))

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_learning_statistics(
        self, user_id: int, content_type: Optional[ContentType] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive learning statistics for a user.

        Args:
            user_id: User's Telegram ID
            content_type: Filter by content type (optional)

        Returns:
            Dictionary containing various statistics
        """
        conditions = [UserProgress.user_id == user_id]
        if content_type:
            conditions.append(UserProgress.content_type == content_type)

        # Get all progress records
        stmt = select(UserProgress).where(and_(*conditions))
        result = await self.db.execute(stmt)
        progress_records = list(result.scalars().all())

        if not progress_records:
            return self._empty_statistics()

        # Calculate statistics
        total_items = len(progress_records)
        learned_items = sum(1 for p in progress_records if p.is_learned)
        mastered_items = sum(1 for p in progress_records if p.is_mastered)
        total_attempts = sum(p.total_attempts for p in progress_records)
        correct_attempts = sum(p.correct_attempts for p in progress_records)

        # Calculate average accuracy
        overall_accuracy = (
            (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        )

        # Count by difficulty
        difficulty_distribution = {}
        for diff_level in DifficultyLevel:
            count = sum(
                1 for p in progress_records if p.current_difficulty == diff_level
            )
            difficulty_distribution[diff_level.value] = count

        # Get review schedule info
        now = datetime.now(timezone.utc)
        due_now = sum(
            1 for p in progress_records if p.needs_review and p.next_review_at <= now
        )
        due_today = sum(
            1
            for p in progress_records
            if p.needs_review and p.next_review_at <= now + timedelta(days=1)
        )

        # Calculate study time
        total_study_time = sum(p.total_study_time_seconds for p in progress_records)

        return {
            "total_items": total_items,
            "learned_items": learned_items,
            "mastered_items": mastered_items,
            "learning_percentage": (
                (learned_items / total_items * 100) if total_items > 0 else 0
            ),
            "mastery_percentage": (
                (mastered_items / total_items * 100) if total_items > 0 else 0
            ),
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "overall_accuracy": overall_accuracy,
            "difficulty_distribution": difficulty_distribution,
            "reviews_due_now": due_now,
            "reviews_due_today": due_today,
            "total_study_time_seconds": total_study_time,
            "total_study_time_hours": round(total_study_time / 3600, 2),
        }

    def _empty_statistics(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_items": 0,
            "learned_items": 0,
            "mastered_items": 0,
            "learning_percentage": 0,
            "mastery_percentage": 0,
            "total_attempts": 0,
            "correct_attempts": 0,
            "overall_accuracy": 0,
            "difficulty_distribution": {level.value: 0 for level in DifficultyLevel},
            "reviews_due_now": 0,
            "reviews_due_today": 0,
            "total_study_time_seconds": 0,
            "total_study_time_hours": 0,
        }

    async def create_learning_session(
        self, user_id: int, session_type: str, content_type: ContentType
    ) -> LearningSession:
        """
        Create a new learning session.

        Args:
            user_id: User's Telegram ID
            session_type: Type of session (lesson, quiz, review, etc.)
            content_type: Type of content being studied

        Returns:
            New LearningSession record
        """
        session = LearningSession(
            user_id=user_id,
            session_type=session_type,
            content_type=content_type,
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(session)
        await self.db.flush()

        logger.info(
            f"Created learning session: user={user_id}, type={session_type}, "
            f"content={content_type.value}"
        )

        return session

    async def complete_learning_session(
        self,
        session_id: int,
        total_questions: int,
        correct_answers: int,
        notes: Optional[str] = None,
    ) -> LearningSession:
        """
        Complete a learning session with results.

        Args:
            session_id: Learning session ID
            total_questions: Total number of questions
            correct_answers: Number of correct answers
            notes: Optional notes about the session

        Returns:
            Updated LearningSession record
        """
        stmt = select(LearningSession).where(LearningSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Learning session {session_id} not found")

        session.total_questions = total_questions
        session.correct_answers = correct_answers
        if notes:
            session.notes = notes

        session.complete_session()

        await self.db.flush()

        logger.info(
            f"Completed learning session: id={session_id}, "
            f"accuracy={session.accuracy_percentage:.1f}%"
        )

        return session

    async def get_learned_character_ids(
        self, user_id: int, content_type: Optional[ContentType] = None
    ) -> Set[str]:
        """
        Get set of character IDs that the user has learned.

        Args:
            user_id: User's Telegram ID
            content_type: Filter by content type (optional)

        Returns:
            Set of content IDs marked as learned
        """
        conditions = [
            UserProgress.user_id == user_id,
            UserProgress.is_learned.is_(True),
        ]

        if content_type:
            conditions.append(UserProgress.content_type == content_type)

        stmt = select(UserProgress.content_id).where(and_(*conditions))

        result = await self.db.execute(stmt)
        return set(result.scalars().all())

    async def get_suggested_review_items(
        self,
        user_id: int,
        content_type: ContentType,
        count: int = 10,
    ) -> List[Tuple[UserProgress, Optional[CharacterData]]]:
        """
        Get suggested items for review with character data.

        Args:
            user_id: User's Telegram ID
            content_type: Type of content to review
            count: Number of items to return

        Returns:
            List of tuples (UserProgress, CharacterData or None)
        """
        # Get due reviews
        due_reviews = await self.get_due_reviews(
            user_id=user_id, content_type=content_type, limit=count
        )

        # Enrich with character data if content service available
        results = []
        for progress in due_reviews:
            character_data = None
            if self.content_service:
                try:
                    character_data = await self.content_service.get_character_by_id(
                        progress.content_id
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch character data for {progress.content_id}: {e}"
                    )

            results.append((progress, character_data))

        return results

    async def reset_progress(
        self, user_id: int, content_id: str, content_type: ContentType
    ) -> None:
        """
        Reset progress for a specific item.

        Args:
            user_id: User's Telegram ID
            content_id: Content identifier
            content_type: Type of content
        """
        stmt = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.content_type == content_type,
                UserProgress.content_id == content_id,
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress:
            # Reset SM-2 parameters
            progress.easiness_factor = Decimal("2.5")
            progress.repetition_count = 0
            progress.interval = 1
            progress.next_review_at = datetime.now(timezone.utc)

            # Reset statistics
            progress.total_attempts = 0
            progress.correct_attempts = 0
            progress.is_learned = False
            progress.is_mastered = False
            progress.needs_review = True

            await self.db.flush()

            logger.info(
                f"Reset progress: user={user_id}, content={content_type.value}:{content_id}"
            )


# Convenience functions


def convert_binary_to_quality_rating(
    is_correct: bool, response_time_ms: Optional[int] = None
) -> int:
    """
    Convert binary correct/incorrect to SM-2 quality rating.

    Args:
        is_correct: Whether answer was correct
        response_time_ms: Response time in milliseconds

    Returns:
        Quality rating (0-5)
    """
    sm2 = SpacedRepetitionSM2()
    rating = sm2.convert_binary_to_quality(is_correct, response_time_ms)
    return int(rating)
