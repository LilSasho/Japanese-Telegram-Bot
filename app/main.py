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
from telegram.ext import Application, CommandHandler, ContextTypes

from app.core.config import Config
from app.core.database import DatabaseManager
from app.bot.handlers.start import start_handler, help_handler


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
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))

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
