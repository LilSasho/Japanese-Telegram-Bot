"""
Configuration management for the Japanese Learning Telegram Bot.

This module handles loading and validation of environment variables,
providing default values and type conversion for bot configuration.
"""

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    # Look for .env file in project root
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv not installed, skip loading
    pass


@dataclass
class Config:
    """Configuration class for the Japanese Learning Telegram Bot."""

    # Telegram Bot Configuration
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    BOT_USERNAME: str = field(default_factory=lambda: os.getenv("BOT_USERNAME", ""))
    WEBHOOK_URL: Optional[str] = field(
        default_factory=lambda: os.getenv("WEBHOOK_URL") or None
    )
    WEBHOOK_PORT: int = field(
        default_factory=lambda: int(os.getenv("WEBHOOK_PORT", "8443"))
    )
    USE_POLLING: bool = field(
        default_factory=lambda: os.getenv("USE_POLLING", "true").lower() == "true"
    )

    # Database Configuration
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///japanese_bot.db")
    )
    DB_POOL_SIZE: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5"))
    )
    DB_MAX_OVERFLOW: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "10"))
    )

    # Learning System Configuration
    DEFAULT_LESSON_SIZE: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_LESSON_SIZE", "5"))
    )
    DEFAULT_QUIZ_SIZE: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_QUIZ_SIZE", "10"))
    )
    SPACED_REPETITION_INTERVALS: List[int] = field(
        default_factory=lambda: [
            int(x)
            for x in os.getenv("SPACED_REPETITION_INTERVALS", "1,3,7,14,30").split(",")
        ]
    )

    # Streak and Progress Settings
    STREAK_RESET_HOURS: int = field(
        default_factory=lambda: int(os.getenv("STREAK_RESET_HOURS", "48"))
    )
    DAILY_GOAL_DEFAULT: int = field(
        default_factory=lambda: int(os.getenv("DAILY_GOAL_DEFAULT", "20"))
    )
    WEEKLY_GOAL_DEFAULT: int = field(
        default_factory=lambda: int(os.getenv("WEEKLY_GOAL_DEFAULT", "100"))
    )

    # Difficulty Thresholds
    EASY_THRESHOLD: int = field(
        default_factory=lambda: int(os.getenv("EASY_THRESHOLD", "90"))
    )
    HARD_THRESHOLD: int = field(
        default_factory=lambda: int(os.getenv("HARD_THRESHOLD", "60"))
    )

    # Reminder System
    DEFAULT_REMINDER_TIMES: List[str] = field(
        default_factory=lambda: os.getenv(
            "DEFAULT_REMINDER_TIMES", "09:00,18:00"
        ).split(",")
    )
    DEFAULT_TIMEZONE: str = field(
        default_factory=lambda: os.getenv("DEFAULT_TIMEZONE", "UTC")
    )
    MAX_REMINDERS_PER_USER: int = field(
        default_factory=lambda: int(os.getenv("MAX_REMINDERS_PER_USER", "5"))
    )

    # Content Paths
    HIRAGANA_DATA_PATH: str = field(
        default_factory=lambda: os.getenv("HIRAGANA_DATA_PATH", "data/hiragana.json")
    )
    KATAKANA_DATA_PATH: str = field(
        default_factory=lambda: os.getenv("KATAKANA_DATA_PATH", "data/katakana.json")
    )
    KANJI_DATA_PATH: str = field(
        default_factory=lambda: os.getenv("KANJI_DATA_PATH", "data/kanji.json")
    )
    VOCABULARY_DATA_PATH: str = field(
        default_factory=lambda: os.getenv(
            "VOCABULARY_DATA_PATH", "data/vocabulary.json"
        )
    )

    # Content Management
    MAX_CONTENT_CACHE_SIZE: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONTENT_CACHE_SIZE", "1000"))
    )

    # External Services (Optional)
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("GOOGLE_TRANSLATE_API_KEY") or None
    )
    PRONUNCIATION_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("PRONUNCIATION_API_KEY") or None
    )
    PRONUNCIATION_API_URL: Optional[str] = field(
        default_factory=lambda: os.getenv("PRONUNCIATION_API_URL") or None
    )
    ANALYTICS_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("ANALYTICS_API_KEY") or None
    )

    # Logging Configuration
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: Optional[str] = field(
        default_factory=lambda: os.getenv("LOG_FILE") or None
    )
    MAX_LOG_SIZE: int = field(
        default_factory=lambda: int(os.getenv("MAX_LOG_SIZE", "10"))
    )  # MB
    LOG_BACKUP_COUNT: int = field(
        default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5"))
    )

    # Security and Rate Limiting
    RATE_LIMIT_ENABLED: bool = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower()
        == "true"
    )
    RATE_LIMIT_MESSAGES_PER_MINUTE: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_MESSAGES_PER_MINUTE", "20"))
    )
    RATE_LIMIT_COMMANDS_PER_MINUTE: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_COMMANDS_PER_MINUTE", "10"))
    )

    # Admin Configuration
    ADMIN_USER_IDS: List[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()
        ]
    )
    ALLOW_NEW_USERS: bool = field(
        default_factory=lambda: os.getenv("ALLOW_NEW_USERS", "true").lower() == "true"
    )
    MAX_USERS: int = field(
        default_factory=lambda: int(os.getenv("MAX_USERS", "0"))
    )  # 0 = unlimited

    # Development Settings
    ENVIRONMENT: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    DEBUG: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true"
    )
    DEV_MODE: bool = field(
        default_factory=lambda: os.getenv("DEV_MODE", "true").lower() == "true"
    )

    # Backup and Maintenance
    BACKUP_ENABLED: bool = field(
        default_factory=lambda: os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    )
    BACKUP_INTERVAL_HOURS: int = field(
        default_factory=lambda: int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    )
    BACKUP_RETENTION_DAYS: int = field(
        default_factory=lambda: int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    )
    BACKUP_PATH: str = field(
        default_factory=lambda: os.getenv("BACKUP_PATH", "backups/")
    )

    # Maintenance Mode
    MAINTENANCE_MODE: bool = field(
        default_factory=lambda: os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
    )
    MAINTENANCE_MESSAGE: str = field(
        default_factory=lambda: os.getenv(
            "MAINTENANCE_MESSAGE",
            "Bot is temporarily under maintenance. Please try again later.",
        )
    )

    # Performance Settings
    HTTP_TIMEOUT: int = field(
        default_factory=lambda: int(os.getenv("HTTP_TIMEOUT", "30"))
    )
    DATABASE_TIMEOUT: int = field(
        default_factory=lambda: int(os.getenv("DATABASE_TIMEOUT", "10"))
    )
    MAX_MEMORY_USAGE_MB: int = field(
        default_factory=lambda: int(os.getenv("MAX_MEMORY_USAGE_MB", "512"))
    )

    # Cache Settings
    REDIS_URL: Optional[str] = field(
        default_factory=lambda: os.getenv("REDIS_URL") or None
    )
    CACHE_TTL_SECONDS: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    )

    # Feature Flags
    FEATURE_VOICE_MESSAGES: bool = field(
        default_factory=lambda: os.getenv("FEATURE_VOICE_MESSAGES", "true").lower()
        == "true"
    )
    FEATURE_IMAGE_RECOGNITION: bool = field(
        default_factory=lambda: os.getenv("FEATURE_IMAGE_RECOGNITION", "false").lower()
        == "true"
    )
    FEATURE_ADVANCED_STATS: bool = field(
        default_factory=lambda: os.getenv("FEATURE_ADVANCED_STATS", "true").lower()
        == "true"
    )
    FEATURE_LEADERBOARD: bool = field(
        default_factory=lambda: os.getenv("FEATURE_LEADERBOARD", "true").lower()
        == "true"
    )
    FEATURE_CULTURAL_NOTES: bool = field(
        default_factory=lambda: os.getenv("FEATURE_CULTURAL_NOTES", "true").lower()
        == "true"
    )
    FEATURE_PRONUNCIATION_CHECK: bool = field(
        default_factory=lambda: os.getenv(
            "FEATURE_PRONUNCIATION_CHECK", "false"
        ).lower()
        == "true"
    )

    # Localization
    DEFAULT_LANGUAGE: str = field(
        default_factory=lambda: os.getenv("DEFAULT_LANGUAGE", "en")
    )
    SUPPORTED_LANGUAGES: List[str] = field(
        default_factory=lambda: os.getenv(
            "SUPPORTED_LANGUAGES", "en,ja,es,fr,de"
        ).split(",")
    )

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure log directory exists if log file is specified
        if self.LOG_FILE:
            log_path = Path(self.LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure backup directory exists if backup is enabled
        if self.BACKUP_ENABLED:
            backup_path = Path(self.BACKUP_PATH)
            backup_path.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def database_is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def database_is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.DATABASE_URL.startswith("postgresql")
