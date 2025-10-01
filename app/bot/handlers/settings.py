"""
Settings and reminder configuration handlers for the Japanese Learning Telegram Bot.

This module provides commands to configure user preferences including
reminder settings, timezone, and notification preferences.
"""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.core.database import DatabaseManager
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /reminders command - configure reminder settings.

    Allows users to enable/disable reminders and set preferences.
    """
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id

    # Get database session
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        user = await session.get(User, user_id)

        if not user:
            await update.message.reply_text(
                "User not found. Please use /start to register first."
            )
            return

        # Build settings message
        status = "✅ Enabled" if user.reminder_enabled else "❌ Disabled"
        reminder_time = user.reminder_time or "09:00"

        message = (
            "⏰ **Reminder Settings**\n\n"
            f"**Status:** {status}\n"
            f"**Time:** {reminder_time} (your local time)\n"
            f"**Threshold:** {user.reminder_threshold or 5} reviews\n\n"
            "Configure your reminder preferences:"
        )

        # Create settings keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔔 Enable" if not user.reminder_enabled else "🔕 Disable",
                    callback_data="reminder_toggle",
                )
            ],
            [InlineKeyboardButton("🕐 Change Time", callback_data="reminder_time")],
            [
                InlineKeyboardButton(
                    "📊 Set Threshold", callback_data="reminder_threshold"
                )
            ],
            [InlineKeyboardButton("✅ Done", callback_data="settings_done")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def toggle_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle reminder enabled/disabled."""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    user_id = query.from_user.id

    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        user = await session.get(User, user_id)

        if user:
            user.reminder_enabled = not user.reminder_enabled
            await session.commit()

            status = "enabled" if user.reminder_enabled else "disabled"
            await query.edit_message_text(
                f"✅ Reminders {status}!\n\nUse /reminders to configure more settings."
            )


async def settings_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close settings menu."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    await query.edit_message_text(
        "✅ Settings saved!\n\nYou can change them anytime with /reminders"
    )
