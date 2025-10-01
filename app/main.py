#!/usr/bin/env python3
"""
Japanese Learning Telegram Bot - Main Application Entry Point

This is the main entry point for the Japanese Learning Telegram Bot.
It initializes the bot, sets up logging, loads configuration, and starts the application.
"""

import asyncio
import logging
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from app.core.config import Config
from app.core.database import DatabaseManager
from app.bot.handlers.start import start_handler, help_handler
from app.bot.handlers.review import (
    review_command,
    start_review_session,
    reveal_answer,
    record_quality_rating,
    cancel_review,
    REVIEWING,
    RATING_QUALITY,
)
from app.bot.handlers.progress import (
    progress_command,
    stats_command,
    streak_command,
)
from app.bot.handlers.settings import (
    reminders_command,
    toggle_reminders,
    settings_done,
)
from app.bot.handlers.lesson import (
    lesson_command,
    start_lesson,
    handle_lesson_navigation,
    show_practice_question,
    reveal_practice_answer,
    record_practice_result,
    cancel_lesson,
    SELECTING_CONTENT,
    LEARNING_CHARACTER,
    PRACTICING,
)


async def main() -> None:
    """Main application entry point."""

    # Load configuration
    config = Config()

    # Set up logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, config.LOG_LEVEL.upper()),
        handlers=[
            logging.StreamHandler(sys.stdout),
            (
                logging.FileHandler(config.LOG_FILE)
                if config.LOG_FILE
                else logging.NullHandler()
            ),
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Japanese Learning Telegram Bot...")

    # Validate bot token
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_bot_token_here":
        logger.error(
            "Bot token not configured! Please set BOT_TOKEN in your .env file."
        )
        sys.exit(1)

    # Initialize database
    try:
        db_manager = DatabaseManager(config.DATABASE_URL)
        await db_manager.init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Register handlers
    # Basic commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))

    # Lesson conversation handler
    lesson_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("lesson", lesson_command)],
        states={
            SELECTING_CONTENT: [
                CallbackQueryHandler(start_lesson, pattern="^lesson_"),
            ],
            LEARNING_CHARACTER: [
                CallbackQueryHandler(handle_lesson_navigation, pattern="^lesson_"),
            ],
            PRACTICING: [
                CallbackQueryHandler(
                    show_practice_question, pattern="^practice_start$"
                ),
                CallbackQueryHandler(
                    reveal_practice_answer, pattern="^practice_reveal$"
                ),
                CallbackQueryHandler(record_practice_result, pattern="^practice_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_lesson)],
    )
    application.add_handler(lesson_conv_handler)

    # Review conversation handler
    review_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("review", review_command)],
        states={
            REVIEWING: [
                CallbackQueryHandler(start_review_session, pattern="^review_"),
            ],
            RATING_QUALITY: [
                CallbackQueryHandler(reveal_answer, pattern="^reveal_answer$"),
                CallbackQueryHandler(record_quality_rating, pattern="^quality_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_review)],
    )
    application.add_handler(review_conv_handler)

    # Progress and statistics commands
    application.add_handler(CommandHandler("progress", progress_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("streak", streak_command))

    # Settings and reminders
    application.add_handler(CommandHandler("reminders", reminders_command))
    application.add_handler(
        CallbackQueryHandler(toggle_reminders, pattern="^reminder_toggle$")
    )
    application.add_handler(
        CallbackQueryHandler(settings_done, pattern="^settings_done$")
    )

    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot."""
        logger.error(f"Exception while handling an update: {context.error}")

    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot started successfully!")

    if config.USE_POLLING:
        logger.info("Running in polling mode...")
        await application.run_polling()
    else:
        logger.info(f"Running in webhook mode on port {config.WEBHOOK_PORT}...")
        await application.run_webhook(
            listen="0.0.0.0", port=config.WEBHOOK_PORT, webhook_url=config.WEBHOOK_URL
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot stopped by user")
    except Exception as e:
        logging.getLogger(__name__).error(f"Fatal error: {e}")
        sys.exit(1)
