"""
Start and help command handlers for the Japanese Learning Telegram Bot.

This module contains the initial user interaction handlers for onboarding
and basic bot information.
"""

from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import DatabaseManager
from app.models.user import User, LanguageCode, LearningLevel


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command - user onboarding."""
    if not update.effective_user or not update.effective_chat:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    language_code = update.effective_user.language_code

    # Get database session
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        # Check if user exists
        existing_user = await session.get(User, user_id)

        if existing_user:
            # Update existing user's activity
            existing_user.update_activity()
            await session.commit()

            welcome_message = (
                f"Welcome back, {existing_user.display_name}! 🎌\n\n"
                f"Ready to continue your Japanese learning journey?\n"
                f"Current level: {existing_user.current_level.value.title()}\n"
                f"Streak: {existing_user.current_streak} days 🔥\n\n"
                "Use /help to see available commands."
            )
        else:
            # Create new user
            new_user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                interface_language=LanguageCode.ENGLISH,
                current_level=LearningLevel.BEGINNER,
                created_at=datetime.now(timezone.utc),
                last_activity_at=datetime.now(timezone.utc),
            )

            session.add(new_user)
            await session.commit()

            welcome_message = (
                f"こんにちは {first_name}! Welcome to your Japanese Learning Bot! 🎌\n\n"
                "I'll help you learn Japanese step by step, starting with hiragana.\n\n"
                "🌸 **What you'll learn:**\n"
                "• Hiragana (46 basic characters)\n"
                "• Katakana (46 characters for foreign words)\n"
                "• Basic Kanji (essential characters)\n"
                "• Vocabulary and phrases\n\n"
                "🎯 **Features:**\n"
                "• Daily lessons and quizzes\n"
                "• Spaced repetition for better memory\n"
                "• Progress tracking and streaks\n"
                "• Cultural notes and tips\n\n"
                "Ready to start your journey? Use /help to see available commands!\n\n"
                "がんばって！(Good luck!)"
            )

    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command - show available commands and features."""
    if not update.effective_user:
        return

    help_message = (
        "🎌 **Japanese Learning Bot - Commands**\n\n"
        "**📚 Learning Commands:**\n"
        "/lesson - Start a new lesson\n"
        "/quiz - Take a practice quiz\n"
        "/review - Review characters you've learned\n"
        "/progress - View your learning progress\n\n"
        "**⚙️ Settings:**\n"
        "/settings - Adjust your learning preferences\n"
        "/reminders - Set up daily reminders\n"
        "/level - Change your learning level\n\n"
        "**📊 Progress & Stats:**\n"
        "/stats - View detailed statistics\n"
        "/streak - Check your learning streak\n"
        "/achievements - View your achievements\n\n"
        "**❓ Support:**\n"
        "/help - Show this help message\n"
        "/about - Learn about this bot\n"
        "/feedback - Send feedback to developers\n\n"
        "**🎯 Quick Start:**\n"
        "New to Japanese? Start with `/lesson` to learn your first hiragana characters!\n\n"
        "Need help? Just type your question and I'll try to assist you!"
    )

    await update.message.reply_text(help_message, parse_mode="Markdown")
