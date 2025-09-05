"""
Conversation states for the Japanese Learning Telegram Bot.

This module defines the conversation states used for managing multi-step
user interactions and maintaining conversation context.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone


class ConversationState(Enum):
    """Main conversation states for the bot."""

    # Initial states
    IDLE = auto()
    MAIN_MENU = auto()

    # Learning states
    LEARNING_TYPE_SELECTION = auto()
    LESSON_DIFFICULTY_SELECTION = auto()
    LESSON_IN_PROGRESS = auto()
    LESSON_REVIEW = auto()

    # Quiz states
    QUIZ_TYPE_SELECTION = auto()
    QUIZ_IN_PROGRESS = auto()
    QUIZ_ANSWER_INPUT = auto()
    QUIZ_RESULTS = auto()

    # Settings states
    SETTINGS_MENU = auto()
    SETTINGS_GOALS = auto()
    SETTINGS_REMINDERS = auto()
    SETTINGS_LANGUAGE = auto()
    SETTINGS_DIFFICULTY = auto()
    SETTINGS_SOUND = auto()
    SETTINGS_CULTURAL = auto()
    SETTINGS_PRIVACY = auto()

    # Progress and review states
    PROGRESS_VIEW = auto()
    REVIEW_SELECTION = auto()
    REVIEW_IN_PROGRESS = auto()

    # Feedback and support states
    FEEDBACK_INPUT = auto()
    HELP_TOPIC_SELECTION = auto()

    # Admin states (for future use)
    ADMIN_PANEL = auto()
    ADMIN_USER_MANAGEMENT = auto()
    ADMIN_CONTENT_MANAGEMENT = auto()


class LessonState(Enum):
    """States specific to lesson progression."""

    INTRO = auto()  # Lesson introduction
    LEARNING = auto()  # Character presentation
    PRACTICE = auto()  # Practice exercises
    ASSESSMENT = auto()  # Knowledge check
    COMPLETION = auto()  # Lesson summary


class QuizState(Enum):
    """States specific to quiz progression."""

    SETUP = auto()  # Quiz configuration
    QUESTION = auto()  # Showing question
    WAITING_ANSWER = auto()  # Waiting for user input
    FEEDBACK = auto()  # Showing answer feedback
    RESULTS = auto()  # Final quiz results


@dataclass
class UserSession:
    """
    Represents a user's current session state and context.

    This class maintains the conversation context for each user,
    including their current state, lesson progress, and temporary data.
    """

    user_id: int
    chat_id: int
    state: ConversationState = ConversationState.IDLE

    # Sub-states for complex interactions
    lesson_state: Optional[LessonState] = None
    quiz_state: Optional[QuizState] = None

    # Session context data
    context_data: Dict[str, Any] = None

    # Timestamps
    started_at: datetime = None
    last_activity_at: datetime = None

    def __post_init__(self):
        """Initialize session with current timestamp."""
        if self.context_data is None:
            self.context_data = {}
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        if self.last_activity_at is None:
            self.last_activity_at = datetime.now(timezone.utc)

    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity_at = datetime.now(timezone.utc)

    def set_state(self, new_state: ConversationState, **context):
        """
        Set new conversation state with optional context data.

        Args:
            new_state: The new conversation state
            **context: Additional context data to store
        """
        self.state = new_state
        self.update_activity()

        # Update context data
        for key, value in context.items():
            self.context_data[key] = value

    def set_lesson_state(self, lesson_state: LessonState, **context):
        """
        Set lesson sub-state with context.

        Args:
            lesson_state: The new lesson state
            **context: Additional context data to store
        """
        self.lesson_state = lesson_state
        self.update_activity()

        # Update context data
        for key, value in context.items():
            self.context_data[key] = value

    def set_quiz_state(self, quiz_state: QuizState, **context):
        """
        Set quiz sub-state with context.

        Args:
            quiz_state: The new quiz state
            **context: Additional context data to store
        """
        self.quiz_state = quiz_state
        self.update_activity()

        # Update context data
        for key, value in context.items():
            self.context_data[key] = value

    def get_context(self, key: str, default=None):
        """
        Get context data by key.

        Args:
            key: Context data key
            default: Default value if key not found

        Returns:
            Context data value or default
        """
        return self.context_data.get(key, default)

    def set_context(self, key: str, value: Any):
        """
        Set context data.

        Args:
            key: Context data key
            value: Context data value
        """
        self.context_data[key] = value
        self.update_activity()

    def clear_context(self, *keys):
        """
        Clear specific context keys or all context data.

        Args:
            *keys: Specific keys to clear. If none provided, clears all.
        """
        if keys:
            for key in keys:
                self.context_data.pop(key, None)
        else:
            self.context_data.clear()

        self.update_activity()

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """
        Check if the session has expired.

        Args:
            timeout_minutes: Session timeout in minutes

        Returns:
            True if session has expired
        """
        if not self.last_activity_at:
            return True

        time_diff = datetime.now(timezone.utc) - self.last_activity_at
        return time_diff.total_seconds() > (timeout_minutes * 60)

    def reset_to_idle(self):
        """Reset session to idle state and clear context."""
        self.state = ConversationState.IDLE
        self.lesson_state = None
        self.quiz_state = None
        self.context_data.clear()
        self.update_activity()


class SessionManager:
    """
    Manages user sessions and conversation states.

    This class provides a simple in-memory session storage.
    For production, consider using Redis or database storage.
    """

    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get_session(self, user_id: int, chat_id: int) -> UserSession:
        """
        Get or create a user session.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID

        Returns:
            UserSession: The user's session
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id, chat_id=chat_id)

        session = self._sessions[user_id]
        session.update_activity()
        return session

    def clear_session(self, user_id: int):
        """
        Clear a user's session.

        Args:
            user_id: Telegram user ID
        """
        self._sessions.pop(user_id, None)

    def cleanup_expired_sessions(self, timeout_minutes: int = 30):
        """
        Remove expired sessions.

        Args:
            timeout_minutes: Session timeout in minutes
        """
        expired_users = [
            user_id
            for user_id, session in self._sessions.items()
            if session.is_expired(timeout_minutes)
        ]

        for user_id in expired_users:
            del self._sessions[user_id]

    def get_active_session_count(self) -> int:
        """
        Get the number of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self._sessions)

    def get_sessions_by_state(self, state: ConversationState) -> list[UserSession]:
        """
        Get all sessions in a specific state.

        Args:
            state: The conversation state to filter by

        Returns:
            List of sessions in the specified state
        """
        return [
            session for session in self._sessions.values() if session.state == state
        ]


# Global session manager instance
session_manager = SessionManager()
