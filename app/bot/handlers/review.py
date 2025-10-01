"""
Review session handlers for the Japanese Learning Telegram Bot.

This module provides interactive review sessions using spaced repetition,
allowing users to review characters that are due based on the SM-2 algorithm.
"""

import logging
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.core.database import DatabaseManager
from app.models.progress import ContentType
from app.services.progress_service import ProgressService
from app.services.content_service import ContentService
from app.utils.spaced_repetition import QualityRating

# Configure logging
logger = logging.getLogger(__name__)

# Conversation states
REVIEWING = 1
RATING_QUALITY = 2


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /review command - start a spaced repetition review session.

    Shows user how many items are due for review and starts the session.
    """
    if not update.effective_user or not update.message:
        return ConversationHandler.END

    user_id = update.effective_user.id

    # Get database session and services
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        # Get review counts by content type
        total_due = 0
        review_breakdown = {}

        for content_type in ContentType:
            count = await progress_service.get_review_count(user_id, content_type)
            if count > 0:
                review_breakdown[content_type.value] = count
                total_due += count

        if total_due == 0:
            await update.message.reply_text(
                "🎉 Great job! You have no reviews due right now.\n\n"
                "Keep learning with /lesson or check your /progress!"
            )
            return ConversationHandler.END

        # Build review summary message
        message_lines = [
            f"📚 **Review Session**",
            f"",
            f"You have **{total_due} items** ready for review:",
            f"",
        ]

        # Add breakdown
        emoji_map = {
            "hiragana": "あ",
            "katakana": "ア",
            "kanji": "漢",
            "vocabulary": "📖",
            "grammar": "📝",
        }

        for content_type, count in review_breakdown.items():
            emoji = emoji_map.get(content_type, "📚")
            message_lines.append(f"{emoji} {content_type.title()}: {count}")

        message_lines.extend(
            [
                "",
                "Reviews use spaced repetition to help you remember! 🧠",
                "",
                "Ready to start? Choose a content type:",
            ]
        )

        # Create inline keyboard for content type selection
        keyboard = []
        for content_type, count in review_breakdown.items():
            emoji = emoji_map.get(content_type, "📚")
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{emoji} {content_type.title()} ({count})",
                        callback_data=f"review_{content_type}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("❌ Cancel", callback_data="review_cancel")]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "\n".join(message_lines), reply_markup=reply_markup, parse_mode="Markdown"
        )

        return REVIEWING


async def start_review_session(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle content type selection and start the review session."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    # Handle cancellation
    if query.data == "review_cancel":
        await query.edit_message_text(
            "Review session cancelled. Use /review when you're ready!"
        )
        return ConversationHandler.END

    # Extract content type from callback data
    content_type_str = query.data.replace("review_", "")
    try:
        content_type = ContentType(content_type_str)
    except ValueError:
        await query.edit_message_text("Invalid content type. Please try /review again.")
        return ConversationHandler.END

    user_id = query.from_user.id

    # Initialize review session in context
    context.user_data["review_session"] = {
        "content_type": content_type,
        "current_index": 0,
        "total_reviewed": 0,
        "correct_count": 0,
        "session_start": datetime.now(timezone.utc),
        "review_items": [],
    }

    # Get review items
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        # Get due reviews with character data
        review_items = await progress_service.get_suggested_review_items(
            user_id=user_id,
            content_type=content_type,
            count=20,  # Limit to 20 items per session
        )

        if not review_items:
            await query.edit_message_text(
                "No items found for review. This might be an error - please try again!"
            )
            return ConversationHandler.END

        # Store review items in session
        context.user_data["review_session"]["review_items"] = review_items
        context.user_data["review_session"]["db_session"] = session
        context.user_data["review_session"]["progress_service"] = progress_service

        # Start first review
        await show_review_question(query, context)

        return RATING_QUALITY


async def show_review_question(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the current review question."""
    session_data = context.user_data.get("review_session", {})
    current_index = session_data.get("current_index", 0)
    review_items = session_data.get("review_items", [])

    if current_index >= len(review_items):
        # Session complete
        await end_review_session(query, context)
        return

    progress, character = review_items[current_index]

    if not character:
        # Skip if character data not available
        session_data["current_index"] += 1
        await show_review_question(query, context)
        return

    # Build question message
    question = (
        f"📝 **Review {current_index + 1}/{len(review_items)}**\n\n"
        f"**Character:** {character.character}\n\n"
        f"What is the reading (romaji)?"
    )

    # Create keyboard with answer reveal
    keyboard = [[InlineKeyboardButton("👁️ Show Answer", callback_data="reveal_answer")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Store current character for answer checking
    context.user_data["review_session"]["current_character"] = character
    context.user_data["review_session"]["review_start_time"] = datetime.now(
        timezone.utc
    )

    await query.edit_message_text(
        question, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def reveal_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reveal the answer and ask for quality rating."""
    query = update.callback_query
    if not query:
        return RATING_QUALITY

    await query.answer()

    session_data = context.user_data.get("review_session", {})
    character = session_data.get("current_character")

    if not character:
        return RATING_QUALITY

    # Calculate response time
    review_start = session_data.get("review_start_time")
    if review_start:
        response_time = (
            datetime.now(timezone.utc) - review_start
        ).total_seconds() * 1000
        session_data["last_response_time"] = int(response_time)

    # Build answer message
    answer_message = (
        f"✅ **Answer:**\n\n"
        f"**Character:** {character.character}\n"
        f"**Romaji:** {character.romaji}\n"
        f"**Pronunciation:** {character.pronunciation}\n"
    )

    if character.meaning:
        answer_message += f"**Meaning:** {character.meaning}\n"

    if character.examples:
        answer_message += f"\n**Example:** {character.examples[0].word} ({character.examples[0].romaji}) - {character.examples[0].meaning}\n"

    answer_message += "\n**How well did you remember?**"

    # Create quality rating keyboard
    keyboard = [
        [InlineKeyboardButton("❌ Forgot completely", callback_data="quality_0")],
        [InlineKeyboardButton("😕 Difficult", callback_data="quality_3")],
        [InlineKeyboardButton("😊 Good", callback_data="quality_4")],
        [InlineKeyboardButton("🎯 Perfect!", callback_data="quality_5")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        answer_message, reply_markup=reply_markup, parse_mode="Markdown"
    )

    return RATING_QUALITY


async def record_quality_rating(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Record the user's quality rating and move to next review."""
    query = update.callback_query
    if not query or not query.data:
        return RATING_QUALITY

    await query.answer()

    # Extract quality rating
    quality = int(query.data.replace("quality_", ""))

    session_data = context.user_data.get("review_session", {})
    character = session_data.get("current_character")
    content_type = session_data.get("content_type")
    response_time_ms = session_data.get("last_response_time")

    if not character or not content_type:
        return RATING_QUALITY

    user_id = query.from_user.id

    # Record the review
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        await progress_service.record_review(
            user_id=user_id,
            content_type=content_type,
            content_id=character.id,
            quality_rating=quality,
            response_time_ms=response_time_ms,
        )

        await session.commit()

    # Update session stats
    session_data["total_reviewed"] += 1
    if quality >= QualityRating.CORRECT_DIFFICULT:
        session_data["correct_count"] += 1

    # Move to next item
    session_data["current_index"] += 1

    # Show next question
    await show_review_question(query, context)

    return RATING_QUALITY


async def end_review_session(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the review session and show summary."""
    session_data = context.user_data.get("review_session", {})

    total_reviewed = session_data.get("total_reviewed", 0)
    correct_count = session_data.get("correct_count", 0)
    session_start = session_data.get("session_start")

    # Calculate session duration
    duration_seconds = 0
    if session_start:
        duration_seconds = int(
            (datetime.now(timezone.utc) - session_start).total_seconds()
        )

    accuracy = (correct_count / total_reviewed * 100) if total_reviewed > 0 else 0

    # Build summary message
    summary = (
        f"🎉 **Review Session Complete!**\n\n"
        f"**Items Reviewed:** {total_reviewed}\n"
        f"**Remembered Well:** {correct_count}/{total_reviewed}\n"
        f"**Accuracy:** {accuracy:.1f}%\n"
        f"**Duration:** {duration_seconds // 60}m {duration_seconds % 60}s\n\n"
    )

    if accuracy >= 90:
        summary += "🌟 Excellent work! Your memory is strong!\n"
    elif accuracy >= 70:
        summary += "👍 Good job! Keep reviewing to strengthen your memory.\n"
    else:
        summary += "💪 Keep practicing! Reviews will help you remember better.\n"

    summary += "\nUse /review again to continue, or /progress to see your stats!"

    # Clear session data
    context.user_data.pop("review_session", None)

    await query.edit_message_text(summary, parse_mode="Markdown")

    return ConversationHandler.END


async def cancel_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the review session."""
    if update.message:
        await update.message.reply_text(
            "Review session cancelled. Use /review when you're ready to continue!"
        )

    # Clear session data
    context.user_data.pop("review_session", None)

    return ConversationHandler.END
