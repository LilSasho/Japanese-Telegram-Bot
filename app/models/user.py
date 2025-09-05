"""
User model for the Japanese Learning Telegram Bot.

This module defines the User model and related database structures
for managing bot users and their preferences.
"""

from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    Boolean,
    Integer,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LanguageCode(str, Enum):
    """Supported language codes."""

    ENGLISH = "en"
    JAPANESE = "ja"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"


class LearningLevel(str, Enum):
    """User learning levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class User(Base):
    """User model for storing Telegram bot users."""

    __tablename__ = "users"

    # Primary key - Telegram user ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Basic user information
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Bot-specific settings
    interface_language: Mapped[LanguageCode] = mapped_column(
        SQLEnum(LanguageCode), default=LanguageCode.ENGLISH, nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Learning preferences
    current_level: Mapped[LearningLevel] = mapped_column(
        SQLEnum(LearningLevel), default=LearningLevel.BEGINNER, nullable=False
    )
    daily_goal: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    lesson_size: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    quiz_size: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Progress tracking
    total_lessons_completed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_quiz_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Learning progress flags
    hiragana_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    katakana_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    kanji_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vocabulary_unlocked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Feature preferences
    reminders_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    sound_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cultural_notes_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Privacy and consent
    analytics_consent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    data_processing_consent: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

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
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_lesson_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Admin and moderation
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    # progress_records = relationship("UserProgress", back_populates="user")
    # reminders = relationship("UserReminder", back_populates="user")

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, username={self.username}, level={self.current_level})>"

    @property
    def display_name(self) -> str:
        """Get the user's display name."""
        if self.username:
            return f"@{self.username}"
        elif self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def is_new_user(self) -> bool:
        """Check if this is a new user (created recently)."""
        if not self.created_at:
            return False

        time_diff = datetime.now(timezone.utc) - self.created_at
        return time_diff.total_seconds() < 86400  # Less than 24 hours

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def update_streak(self, completed_today: bool = True) -> None:
        """Update the user's learning streak.

        Args:
            completed_today: Whether user completed learning activity today
        """
        if completed_today:
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
        else:
            self.current_streak = 0

        self.updated_at = datetime.now(timezone.utc)
