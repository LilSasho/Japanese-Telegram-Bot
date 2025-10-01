"""
Reminder service for the Japanese Learning Telegram Bot.

This module provides automated reminder functionality including:
- Review reminder scheduling based on spaced repetition intervals
- Daily study streak tracking and notifications
- Customizable reminder times and frequency
- Integration with progress tracking for intelligent reminders
"""

import logging
import asyncio
from datetime import datetime, time, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.progress import ContentType
from app.services.progress_service import ProgressService


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ReminderConfig:
    """Configuration for user reminders."""

    user_id: int
    enabled: bool = True
    preferred_time: time = time(hour=9, minute=0)  # 9 AM UTC default
    timezone_offset: int = 0  # Offset from UTC in hours
    daily_reminder: bool = True
    review_threshold: int = 5  # Remind when this many reviews are due
    min_hours_between_reminders: int = 4


@dataclass
class ReminderNotification:
    """A reminder notification to be sent."""

    user_id: int
    notification_type: str  # "daily_review", "due_items", "streak"
    message: str
    priority: int = 1  # 1=low, 2=normal, 3=high
    metadata: Optional[Dict] = None


class ReminderService:
    """Service for managing learning reminders and notifications."""

    def __init__(self, db_session: AsyncSession, progress_service: ProgressService):
        """
        Initialize the reminder service.

        Args:
            db_session: SQLAlchemy async database session
            progress_service: Progress service for checking due reviews
        """
        self.db = db_session
        self.progress_service = progress_service
        self._user_configs: Dict[int, ReminderConfig] = {}
        self._last_reminder_times: Dict[int, datetime] = {}
        self._running = False

    async def start_reminder_loop(self, check_interval_minutes: int = 15) -> None:
        """
        Start the reminder checking loop.

        Args:
            check_interval_minutes: How often to check for due reminders
        """
        if self._running:
            logger.warning("Reminder loop already running")
            return

        self._running = True
        logger.info(
            f"Starting reminder loop (checking every {check_interval_minutes} minutes)"
        )

        try:
            while self._running:
                await self._check_and_send_reminders()
                await asyncio.sleep(check_interval_minutes * 60)
        except asyncio.CancelledError:
            logger.info("Reminder loop cancelled")
            self._running = False
            raise
        except Exception as e:
            logger.error(f"Error in reminder loop: {e}", exc_info=True)
            self._running = False

    def stop_reminder_loop(self) -> None:
        """Stop the reminder checking loop."""
        logger.info("Stopping reminder loop")
        self._running = False

    async def _check_and_send_reminders(self) -> List[ReminderNotification]:
        """
        Check all users and generate reminders as needed.

        Returns:
            List of notifications to send
        """
        notifications = []

        # Get all active users with reminder preferences
        stmt = select(User).where(User.reminder_enabled.is_(True))
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        logger.debug(f"Checking reminders for {len(users)} users")

        for user in users:
            try:
                user_notifications = await self._check_user_reminders(user)
                notifications.extend(user_notifications)
            except Exception as e:
                logger.error(f"Error checking reminders for user {user.id}: {e}")

        if notifications:
            logger.info(f"Generated {len(notifications)} reminder notifications")

        return notifications

    async def _check_user_reminders(self, user: User) -> List[ReminderNotification]:
        """
        Check and generate reminders for a specific user.

        Args:
            user: User object

        Returns:
            List of notifications for this user
        """
        notifications = []
        now = datetime.now(timezone.utc)

        # Get user's reminder config
        config = await self._get_user_config(user.id)

        if not config.enabled:
            return notifications

        # Check if enough time has passed since last reminder
        last_reminder = self._last_reminder_times.get(user.id)
        if last_reminder:
            hours_since_last = (now - last_reminder).total_seconds() / 3600
            if hours_since_last < config.min_hours_between_reminders:
                return notifications

        # Check for due reviews
        due_count = await self.progress_service.get_review_count(user.id)

        if due_count >= config.review_threshold:
            notification = await self._create_review_reminder(
                user.id, due_count, config
            )
            notifications.append(notification)
            self._last_reminder_times[user.id] = now

        # Check for daily reminder at preferred time
        if config.daily_reminder and self._is_preferred_time(config, now):
            notification = await self._create_daily_reminder(user.id, due_count)
            if notification:
                notifications.append(notification)

        return notifications

    async def _get_user_config(self, user_id: int) -> ReminderConfig:
        """
        Get reminder configuration for a user.

        Args:
            user_id: User's Telegram ID

        Returns:
            ReminderConfig object
        """
        # Check cache first
        if user_id in self._user_configs:
            return self._user_configs[user_id]

        # Load from database
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Return default config
            config = ReminderConfig(user_id=user_id, enabled=False)
        else:
            # Parse reminder time from user preferences
            reminder_time = self._parse_reminder_time(user.reminder_time)

            config = ReminderConfig(
                user_id=user_id,
                enabled=user.reminder_enabled,
                preferred_time=reminder_time,
                timezone_offset=user.timezone_offset or 0,
                daily_reminder=user.daily_reminder,
                review_threshold=user.reminder_threshold or 5,
            )

        # Cache it
        self._user_configs[user_id] = config

        return config

    def _parse_reminder_time(self, time_str: Optional[str]) -> time:
        """
        Parse reminder time string to time object.

        Args:
            time_str: Time string in format "HH:MM"

        Returns:
            time object (defaults to 9:00 AM if parsing fails)
        """
        if not time_str:
            return time(hour=9, minute=0)

        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour=hour, minute=minute)
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse reminder time: {time_str}")
            return time(hour=9, minute=0)

    def _is_preferred_time(self, config: ReminderConfig, now: datetime) -> bool:
        """
        Check if current time matches user's preferred reminder time.

        Args:
            config: User's reminder configuration
            now: Current datetime

        Returns:
            True if current time is within the preferred hour
        """
        # Adjust for user's timezone
        user_time = now + timedelta(hours=config.timezone_offset)

        # Check if we're within the preferred hour
        preferred_hour = config.preferred_time.hour
        current_hour = user_time.hour

        return current_hour == preferred_hour

    async def _create_review_reminder(
        self, user_id: int, due_count: int, config: ReminderConfig
    ) -> ReminderNotification:
        """
        Create a review reminder notification.

        Args:
            user_id: User's Telegram ID
            due_count: Number of items due for review
            config: User's reminder configuration

        Returns:
            ReminderNotification object
        """
        # Get breakdown by content type
        review_breakdown = await self._get_review_breakdown(user_id)

        message_parts = [
            f"📚 You have {due_count} items ready for review!",
            "",
        ]

        if review_breakdown:
            message_parts.append("Breakdown:")
            for content_type, count in review_breakdown.items():
                emoji = self._get_content_emoji(content_type)
                message_parts.append(f"{emoji} {content_type.title()}: {count}")

        message_parts.extend(
            [
                "",
                "Review now to strengthen your memory! 💪",
            ]
        )

        return ReminderNotification(
            user_id=user_id,
            notification_type="due_items",
            message="\n".join(message_parts),
            priority=2 if due_count > 20 else 1,
            metadata={"due_count": due_count, "breakdown": review_breakdown},
        )

    async def _create_daily_reminder(
        self, user_id: int, due_count: int
    ) -> Optional[ReminderNotification]:
        """
        Create a daily study reminder.

        Args:
            user_id: User's Telegram ID
            due_count: Number of items due for review

        Returns:
            ReminderNotification object or None
        """
        stats = await self.progress_service.get_learning_statistics(user_id)

        # Skip if no progress at all
        if stats["total_items"] == 0:
            return None

        message_parts = [
            "🌅 Good morning! Time for your daily Japanese study session.",
            "",
        ]

        if due_count > 0:
            message_parts.append(f"📝 {due_count} items ready for review")

        # Add motivational stats
        learning_pct = stats["learning_percentage"]
        if learning_pct > 0:
            message_parts.append(f"📊 Progress: {learning_pct:.1f}% of items learned")

        message_parts.extend(
            [
                "",
                "Keep up the great work! 🎯",
            ]
        )

        return ReminderNotification(
            user_id=user_id,
            notification_type="daily_review",
            message="\n".join(message_parts),
            priority=1,
            metadata={"due_count": due_count, "stats": stats},
        )

    async def _get_review_breakdown(self, user_id: int) -> Dict[str, int]:
        """
        Get breakdown of due reviews by content type.

        Args:
            user_id: User's Telegram ID

        Returns:
            Dictionary mapping content type to count
        """
        breakdown = {}

        for content_type in ContentType:
            count = await self.progress_service.get_review_count(
                user_id, content_type=content_type
            )
            if count > 0:
                breakdown[content_type.value] = count

        return breakdown

    def _get_content_emoji(self, content_type: str) -> str:
        """Get emoji for content type."""
        emoji_map = {
            "hiragana": "あ",
            "katakana": "ア",
            "kanji": "漢",
            "vocabulary": "📖",
            "grammar": "📝",
        }
        return emoji_map.get(content_type, "📚")

    async def update_user_config(
        self,
        user_id: int,
        enabled: Optional[bool] = None,
        preferred_time: Optional[time] = None,
        timezone_offset: Optional[int] = None,
        daily_reminder: Optional[bool] = None,
        review_threshold: Optional[int] = None,
    ) -> None:
        """
        Update reminder configuration for a user.

        Args:
            user_id: User's Telegram ID
            enabled: Enable/disable reminders
            preferred_time: Preferred reminder time
            timezone_offset: User's timezone offset from UTC
            daily_reminder: Enable/disable daily reminders
            review_threshold: Number of due items to trigger reminder
        """
        # Get existing config
        config = await self._get_user_config(user_id)

        # Update fields
        if enabled is not None:
            config.enabled = enabled
        if preferred_time is not None:
            config.preferred_time = preferred_time
        if timezone_offset is not None:
            config.timezone_offset = timezone_offset
        if daily_reminder is not None:
            config.daily_reminder = daily_reminder
        if review_threshold is not None:
            config.review_threshold = review_threshold

        # Update cache
        self._user_configs[user_id] = config

        # Update database
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.reminder_enabled = config.enabled
            user.reminder_time = config.preferred_time.strftime("%H:%M")
            user.timezone_offset = config.timezone_offset
            user.daily_reminder = config.daily_reminder
            user.reminder_threshold = config.review_threshold
            await self.db.flush()

        logger.info(f"Updated reminder config for user {user_id}")

    async def send_immediate_reminder(
        self, user_id: int, notification_type: str, custom_message: Optional[str] = None
    ) -> ReminderNotification:
        """
        Send an immediate reminder to a user.

        Args:
            user_id: User's Telegram ID
            notification_type: Type of notification
            custom_message: Custom message (optional)

        Returns:
            ReminderNotification object
        """
        if custom_message:
            message = custom_message
        else:
            # Generate appropriate message based on type
            if notification_type == "due_items":
                due_count = await self.progress_service.get_review_count(user_id)
                config = await self._get_user_config(user_id)
                return await self._create_review_reminder(user_id, due_count, config)
            elif notification_type == "daily_review":
                due_count = await self.progress_service.get_review_count(user_id)
                return await self._create_daily_reminder(user_id, due_count)
            else:
                message = "Time to study Japanese! 📚"

        return ReminderNotification(
            user_id=user_id,
            notification_type=notification_type,
            message=message,
            priority=2,
        )


# Helper function to create formatted reminder message
def format_review_summary(
    due_count: int,
    learned_count: int,
    mastered_count: int,
    streak_days: int = 0,
) -> str:
    """
    Format a review summary message.

    Args:
        due_count: Number of items due for review
        learned_count: Number of items learned
        mastered_count: Number of items mastered
        streak_days: Current study streak

    Returns:
        Formatted message string
    """
    lines = [
        "📊 Your Learning Summary",
        "=" * 30,
        f"📝 Reviews Due: {due_count}",
        f"✅ Items Learned: {learned_count}",
        f"⭐ Items Mastered: {mastered_count}",
    ]

    if streak_days > 0:
        lines.append(f"🔥 Study Streak: {streak_days} days")

    return "\n".join(lines)
