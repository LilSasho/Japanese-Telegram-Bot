"""
Lesson handlers for the Japanese Learning Telegram Bot.

This module provides interactive lessons for learning new Japanese characters,
including character introduction, mnemonics, examples, and practice exercises.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.core.database import DatabaseManager
from app.models.progress import ContentType
from app.services.progress_service import ProgressService
from app.services.content_service import (
    ContentService,
    ContentType as ServiceContentType,
)
from app.utils.spaced_repetition import QualityRating

# Configure logging
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_CONTENT, LEARNING_CHARACTER, PRACTICING = range(3)


async def lesson_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /lesson command - start a new lesson.

    Shows available content types and allows user to select what to learn.
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

        # Get learned character IDs
        learned_hiragana = await progress_service.get_learned_character_ids(
            user_id, ContentType.HIRAGANA
        )
        learned_katakana = await progress_service.get_learned_character_ids(
            user_id, ContentType.KATAKANA
        )

        # Get content statistics
        stats = await content_service.get_content_statistics()

        # Build lesson selection message
        message_lines = [
            "📚 **New Lesson**",
            "",
            "Choose what you'd like to learn:",
            "",
        ]

        # Create keyboard with available content
        keyboard = []

        # Hiragana option
        total_hiragana = stats.get("content_types", {}).get("hiragana", 0)
        if total_hiragana > 0:
            learned_count = len(learned_hiragana)
            remaining = total_hiragana - learned_count
            if remaining > 0:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"あ Hiragana ({learned_count}/{total_hiragana} learned)",
                            callback_data="lesson_hiragana",
                        )
                    ]
                )

        # Katakana option
        total_katakana = stats.get("content_types", {}).get("katakana", 0)
        if total_katakana > 0:
            learned_count = len(learned_katakana)
            remaining = total_katakana - learned_count
            if remaining > 0:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"ア Katakana ({learned_count}/{total_katakana} learned)",
                            callback_data="lesson_katakana",
                        )
                    ]
                )

        if not keyboard:
            await update.message.reply_text(
                "🎉 Congratulations! You've learned all available characters!\n\n"
                "Use /review to practice what you've learned."
            )
            return ConversationHandler.END

        keyboard.append(
            [InlineKeyboardButton("❌ Cancel", callback_data="lesson_cancel")]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "\n".join(message_lines), reply_markup=reply_markup, parse_mode="Markdown"
        )

        return SELECTING_CONTENT


async def start_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle content type selection and start the lesson."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    # Handle cancellation
    if query.data == "lesson_cancel":
        await query.edit_message_text(
            "Lesson cancelled. Use /lesson when you're ready!"
        )
        return ConversationHandler.END

    # Extract content type
    content_type_str = query.data.replace("lesson_", "")
    try:
        content_type = ServiceContentType(content_type_str.upper())
        progress_content_type = ContentType(content_type_str.upper())
    except ValueError:
        await query.edit_message_text("Invalid content type. Please try /lesson again.")
        return ConversationHandler.END

    user_id = query.from_user.id

    # Get next characters to learn
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        # Get learned characters
        learned_chars = await progress_service.get_learned_character_ids(
            user_id, progress_content_type
        )

        # Get next characters to learn (5 per lesson)
        next_chars = await content_service.get_next_characters_to_learn(
            learned_characters=learned_chars, content_type=content_type, count=5
        )

        if not next_chars:
            await query.edit_message_text(
                "No new characters available. Try reviewing what you've learned with /review!"
            )
            return ConversationHandler.END

        # Initialize lesson session
        context.user_data["lesson_session"] = {
            "content_type": progress_content_type,
            "characters": next_chars,
            "current_index": 0,
            "practice_results": [],
            "session_start": datetime.now(timezone.utc),
        }

        # Show first character
        await show_character_lesson(query, context)

        return LEARNING_CHARACTER


async def show_character_lesson(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a character lesson with all learning aids."""
    session_data = context.user_data.get("lesson_session", {})
    current_index = session_data.get("current_index", 0)
    characters = session_data.get("characters", [])

    if current_index >= len(characters):
        # All characters learned, move to practice
        await start_practice_session(query, context)
        return

    character = characters[current_index]

    # Build lesson message
    message_lines = [
        f"📖 **Lesson {current_index + 1}/{len(characters)}**",
        "",
        f"**Character:** {character.character}",
        f"**Reading:** {character.romaji}",
        f"**Pronunciation:** {character.pronunciation}",
    ]

    if character.meaning:
        message_lines.append(f"**Meaning:** {character.meaning}")

    message_lines.append("")

    # Add mnemonic if available
    if character.mnemonics:
        message_lines.extend(["💡 **Memory Aid:**", character.mnemonics, ""])

    # Add examples
    if character.examples:
        message_lines.append("📝 **Examples:**")
        for example in character.examples[:2]:  # Show first 2 examples
            message_lines.append(
                f"• {example.word} ({example.romaji}) - {example.meaning}"
            )
        message_lines.append("")

    # Add common mistakes if available
    if character.common_mistakes:
        message_lines.append("⚠️ **Common Mistakes:**")
        for mistake in character.common_mistakes[:2]:
            message_lines.append(f"• {mistake}")
        message_lines.append("")

    message_lines.extend(
        [
            "Take your time to study this character.",
            "When you're ready, let's practice!",
        ]
    )

    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("✅ Got it! Next →", callback_data="lesson_next")],
        [InlineKeyboardButton("📖 Review Again", callback_data="lesson_review")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "\n".join(message_lines), reply_markup=reply_markup, parse_mode="Markdown"
    )


async def handle_lesson_navigation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle lesson navigation (next, review)."""
    query = update.callback_query
    if not query or not query.data:
        return LEARNING_CHARACTER

    await query.answer()

    session_data = context.user_data.get("lesson_session", {})

    if query.data == "lesson_next":
        # Move to next character
        session_data["current_index"] += 1
        await show_character_lesson(query, context)
        return LEARNING_CHARACTER

    elif query.data == "lesson_review":
        # Show same character again
        await show_character_lesson(query, context)
        return LEARNING_CHARACTER

    return LEARNING_CHARACTER


async def start_practice_session(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start practice session after learning all characters."""
    session_data = context.user_data.get("lesson_session", {})
    characters = session_data.get("characters", [])

    # Reset for practice
    session_data["current_index"] = 0
    session_data["practice_results"] = []

    message = (
        "🎯 **Practice Time!**\n\n"
        f"You've learned {len(characters)} new characters.\n"
        "Let's practice to help you remember them!\n\n"
        "I'll show you each character and you tell me if you remember the reading."
    )

    keyboard = [
        [InlineKeyboardButton("▶️ Start Practice", callback_data="practice_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        message, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def show_practice_question(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a practice question."""
    session_data = context.user_data.get("lesson_session", {})
    current_index = session_data.get("current_index", 0)
    characters = session_data.get("characters", [])

    if current_index >= len(characters):
        # Practice complete
        await complete_lesson(query, context)
        return ConversationHandler.END

    character = characters[current_index]

    question = (
        f"📝 **Practice {current_index + 1}/{len(characters)}**\n\n"
        f"**Character:** {character.character}\n\n"
        "What is the reading (romaji)?"
    )

    keyboard = [
        [InlineKeyboardButton("👁️ Show Answer", callback_data="practice_reveal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["lesson_session"]["practice_start_time"] = datetime.now(
        timezone.utc
    )

    await query.edit_message_text(
        question, reply_markup=reply_markup, parse_mode="Markdown"
    )

    return PRACTICING


async def reveal_practice_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Reveal practice answer and ask for self-assessment."""
    query = update.callback_query
    if not query:
        return PRACTICING

    await query.answer()

    session_data = context.user_data.get("lesson_session", {})
    current_index = session_data.get("current_index", 0)
    characters = session_data.get("characters", [])
    character = characters[current_index]

    answer = (
        f"✅ **Answer:**\n\n"
        f"**Character:** {character.character}\n"
        f"**Reading:** {character.romaji}\n"
        f"**Pronunciation:** {character.pronunciation}\n\n"
        "Did you get it right?"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Yes, I got it!", callback_data="practice_correct")],
        [InlineKeyboardButton("❌ No, I forgot", callback_data="practice_incorrect")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        answer, reply_markup=reply_markup, parse_mode="Markdown"
    )

    return PRACTICING


async def record_practice_result(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Record practice result and move to next question."""
    query = update.callback_query
    if not query or not query.data:
        return PRACTICING

    await query.answer()

    session_data = context.user_data.get("lesson_session", {})
    current_index = session_data.get("current_index", 0)
    characters = session_data.get("characters", [])
    character = characters[current_index]
    content_type = session_data.get("content_type")

    # Determine if correct
    is_correct = query.data == "practice_correct"

    # Calculate response time
    start_time = session_data.get("practice_start_time")
    response_time_ms = None
    if start_time:
        response_time_ms = int(
            (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        )

    # Record to database
    user_id = query.from_user.id
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        # Convert binary to quality rating
        quality = (
            QualityRating.PERFECT if is_correct else QualityRating.INCORRECT_REMEMBERED
        )

        await progress_service.record_review(
            user_id=user_id,
            content_type=content_type,
            content_id=character.id,
            quality_rating=int(quality),
            response_time_ms=response_time_ms,
        )

        await session.commit()

    # Store result
    session_data["practice_results"].append(is_correct)
    session_data["current_index"] += 1

    # Show next question
    await show_practice_question(query, context)

    return PRACTICING


async def complete_lesson(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Complete the lesson and show summary."""
    session_data = context.user_data.get("lesson_session", {})
    characters = session_data.get("characters", [])
    results = session_data.get("practice_results", [])
    session_start = session_data.get("session_start")

    correct_count = sum(results)
    total = len(results)
    accuracy = (correct_count / total * 100) if total > 0 else 0

    # Calculate duration
    duration_seconds = 0
    if session_start:
        duration_seconds = int(
            (datetime.now(timezone.utc) - session_start).total_seconds()
        )

    summary = (
        f"🎉 **Lesson Complete!**\n\n"
        f"**New Characters Learned:** {len(characters)}\n"
        f"**Practice Accuracy:** {correct_count}/{total} ({accuracy:.0f}%)\n"
        f"**Duration:** {duration_seconds // 60}m {duration_seconds % 60}s\n\n"
    )

    if accuracy == 100:
        summary += "⭐ Perfect score! Excellent work!\n"
    elif accuracy >= 80:
        summary += "👍 Great job! Keep practicing!\n"
    else:
        summary += "💪 Good start! Review these characters with /review\n"

    summary += "\nUse /lesson to learn more, or /review to practice!"

    # Clear session data
    context.user_data.pop("lesson_session", None)

    await query.edit_message_text(summary, parse_mode="Markdown")


async def cancel_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the lesson."""
    if update.message:
        await update.message.reply_text(
            "Lesson cancelled. Use /lesson when you're ready to learn!"
        )

    # Clear session data
    context.user_data.pop("lesson_session", None)

    return ConversationHandler.END
