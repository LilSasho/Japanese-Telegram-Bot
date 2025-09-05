"""
Progress tracking models for the Japanese Learning Telegram Bot.

This module defines models for tracking user learning progress,
including individual character/word proficiency and overall statistics.
"""

from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    Boolean,
    Integer,
    Text,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentType(str, Enum):
    """Types of learning content."""

    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    KANJI = "kanji"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"


class DifficultyLevel(str, Enum):
    """Difficulty levels for spaced repetition."""

    VERY_EASY = "very_easy"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    VERY_HARD = "very_hard"


class QuizResult(str, Enum):
    """Quiz answer results."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIALLY_CORRECT = "partially_correct"
    SKIPPED = "skipped"


class UserProgress(Base):
    """Track individual user progress on specific content items."""

    __tablename__ = "user_progress"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    # Content identification
    content_type: Mapped[ContentType] = mapped_column(
        SQLEnum(ContentType), nullable=False
    )
    content_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "hiragana_a", "kanji_水"

    # Spaced repetition data (SM-2 algorithm)
    easiness_factor: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("2.5"), nullable=False
    )
    repetition_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interval: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # Days until next review

    # Performance tracking
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_difficulty: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel), default=DifficultyLevel.NORMAL, nullable=False
    )

    # Time tracking
    total_study_time_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    average_response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Status flags
    is_learned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    # user = relationship("User", back_populates="progress_records")

    # Database indexes for performance
    __table_args__ = (
        Index("idx_user_content", "user_id", "content_type", "content_id"),
        Index("idx_next_review", "user_id", "next_review_at"),
        Index("idx_needs_review", "user_id", "needs_review"),
    )

    def __repr__(self) -> str:
        """String representation of the progress record."""
        return f"<UserProgress(user_id={self.user_id}, content={self.content_type}:{self.content_id})>"

    @property
    def accuracy_percentage(self) -> float:
        """Calculate accuracy percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_attempts / self.total_attempts) * 100.0

    @property
    def is_due_for_review(self) -> bool:
        """Check if this item is due for review."""
        if not self.needs_review:
            return False
        return datetime.now(timezone.utc) >= self.next_review_at

    def update_progress(
        self, is_correct: bool, response_time_ms: Optional[int] = None
    ) -> None:
        """Update progress based on user performance.

        Args:
            is_correct: Whether the user answered correctly
            response_time_ms: Response time in milliseconds
        """
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1

        # Update response time (running average)
        if response_time_ms is not None:
            if self.average_response_time_ms is None:
                self.average_response_time_ms = response_time_ms
            else:
                # Exponential moving average
                alpha = 0.3
                self.average_response_time_ms = int(
                    alpha * response_time_ms
                    + (1 - alpha) * self.average_response_time_ms
                )

        # Update spaced repetition data using SM-2 algorithm
        self._update_spaced_repetition(is_correct)

        # Update status flags
        self._update_learning_status()

        # Update timestamps
        self.last_reviewed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def _update_spaced_repetition(self, is_correct: bool) -> None:
        """Update spaced repetition intervals using SM-2 algorithm.

        Args:
            is_correct: Whether the answer was correct
        """
        if is_correct:
            if self.repetition_count == 0:
                self.interval = 1
            elif self.repetition_count == 1:
                self.interval = 6
            else:
                self.interval = int(self.interval * float(self.easiness_factor))

            self.repetition_count += 1

            # Update easiness factor (make it easier if correct)
            self.easiness_factor = max(
                Decimal("1.3"), self.easiness_factor + Decimal("0.1")
            )

        else:
            # Reset repetition count and make it harder
            self.repetition_count = 0
            self.interval = 1
            self.easiness_factor = max(
                Decimal("1.3"), self.easiness_factor - Decimal("0.2")
            )

        # Set next review date
        next_review = datetime.now(timezone.utc)
        next_review = next_review.replace(
            hour=0, minute=0, second=0, microsecond=0
        )  # Start of day

        from datetime import timedelta

        self.next_review_at = next_review + timedelta(days=self.interval)

    def _update_learning_status(self) -> None:
        """Update learning status flags based on performance."""
        # Consider learned if accuracy > 80% and attempted at least 3 times
        if self.total_attempts >= 3 and self.accuracy_percentage > 80:
            self.is_learned = True

        # Consider mastered if accuracy > 95% and attempted at least 5 times
        if self.total_attempts >= 5 and self.accuracy_percentage > 95:
            self.is_mastered = True

        # Update difficulty based on accuracy
        if self.accuracy_percentage >= 95:
            self.current_difficulty = DifficultyLevel.VERY_EASY
        elif self.accuracy_percentage >= 85:
            self.current_difficulty = DifficultyLevel.EASY
        elif self.accuracy_percentage >= 70:
            self.current_difficulty = DifficultyLevel.NORMAL
        elif self.accuracy_percentage >= 50:
            self.current_difficulty = DifficultyLevel.HARD
        else:
            self.current_difficulty = DifficultyLevel.VERY_HARD


class LearningSession(Base):
    """Track individual learning sessions."""

    __tablename__ = "learning_sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    # Session data
    session_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # lesson, quiz, review, etc.
    content_type: Mapped[ContentType] = mapped_column(
        SQLEnum(ContentType), nullable=False
    )

    # Performance metrics
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Additional data
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation of the learning session."""
        return f"<LearningSession(user_id={self.user_id}, type={self.session_type})>"

    @property
    def accuracy_percentage(self) -> float:
        """Calculate session accuracy percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100.0

    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.completed_at is not None

    def complete_session(self) -> None:
        """Mark session as completed."""
        if not self.is_completed:
            self.completed_at = datetime.now(timezone.utc)
            if self.started_at:
                duration = self.completed_at - self.started_at
                self.duration_seconds = int(duration.total_seconds())
