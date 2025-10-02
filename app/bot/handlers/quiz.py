"""
Quiz handlers for the Japanese Learning Telegram Bot.

This module provides interactive quiz functionality with three modes:
- Multiple choice: Select the correct answer from options
- Typing practice: Type the romaji for a character
- Character recognition: Identify the character from romaji
"""

import logging
from typing import Optional, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.core.database import DatabaseManager
from app.models.progress import ContentType
from app.services.progress_service import ProgressService
from app.services.content_service import (
    ContentService,
    ContentType as ServiceContentType,
)
from app.services.quiz_service import (
    QuizService,
    QuizMode,
    QuizDifficulty,
    QuizSession,
)

# Configure logging
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_MODE, SELECTING_DIFFICULTY, SELECTING_CONTENT, ANSWERING, SHOW_RESULT = range(
    5
)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /quiz command - start a new quiz.

    Shows quiz mode selection.
    """
    if not update.effective_user or not update.message:
        return ConversationHandler.END

    # Build quiz mode selection message
    message_lines = [
        "🎯 **Quiz Time!**",
        "",
        "Choose your quiz mode:",
        "",
        "**Multiple Choice** - Select the correct romaji",
        "**Typing Practice** - Type the romaji yourself",
        "**Recognition** - Identify the character from romaji",
    ]

    keyboard = [
        [InlineKeyboardButton("🔤 Multiple Choice", callback_data="quiz_mode_mc")],
        [InlineKeyboardButton("⌨️ Typing Practice", callback_data="quiz_mode_typing")],
        [InlineKeyboardButton("👁️ Recognition", callback_data="quiz_mode_recog")],
        [InlineKeyboardButton("❌ Cancel", callback_data="quiz_cancel")],
    ]

    await update.message.reply_text(
        "\n".join(message_lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return SELECTING_MODE


async def quiz_mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quiz mode selection."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    # Parse mode
    if query.data == "quiz_cancel":
        await query.edit_message_text("Quiz cancelled. Use /quiz to try again!")
        return ConversationHandler.END

    mode_mapping = {
        "quiz_mode_mc": QuizMode.MULTIPLE_CHOICE,
        "quiz_mode_typing": QuizMode.TYPING,
        "quiz_mode_recog": QuizMode.RECOGNITION,
    }

    mode = mode_mapping.get(query.data)
    if not mode:
        await query.edit_message_text("Invalid mode. Use /quiz to start again.")
        return ConversationHandler.END

    # Store mode in context
    context.user_data["quiz_mode"] = mode

    # Show difficulty selection
    keyboard = [
        [InlineKeyboardButton("😊 Easy", callback_data="quiz_diff_easy")],
        [InlineKeyboardButton("😐 Medium", callback_data="quiz_diff_medium")],
        [InlineKeyboardButton("😤 Hard", callback_data="quiz_diff_hard")],
        [InlineKeyboardButton("❌ Cancel", callback_data="quiz_cancel")],
    ]

    mode_names = {
        QuizMode.MULTIPLE_CHOICE: "Multiple Choice",
        QuizMode.TYPING: "Typing Practice",
        QuizMode.RECOGNITION: "Character Recognition",
    }

    await query.edit_message_text(
        f"**{mode_names[mode]}** selected!\n\nChoose difficulty level:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return SELECTING_DIFFICULTY


async def quiz_difficulty_selected(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle difficulty selection."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    if query.data == "quiz_cancel":
        await query.edit_message_text("Quiz cancelled. Use /quiz to try again!")
        return ConversationHandler.END

    # Parse difficulty
    diff_mapping = {
        "quiz_diff_easy": QuizDifficulty.EASY,
        "quiz_diff_medium": QuizDifficulty.MEDIUM,
        "quiz_diff_hard": QuizDifficulty.HARD,
    }

    difficulty = diff_mapping.get(query.data)
    if not difficulty:
        await query.edit_message_text("Invalid difficulty. Use /quiz to start again.")
        return ConversationHandler.END

    # Store difficulty in context
    context.user_data["quiz_difficulty"] = difficulty

    # Show content type selection
    keyboard = [
        [InlineKeyboardButton("あ Hiragana", callback_data="quiz_content_hiragana")],
        [InlineKeyboardButton("ア Katakana", callback_data="quiz_content_katakana")],
        [InlineKeyboardButton("❌ Cancel", callback_data="quiz_cancel")],
    ]

    await query.edit_message_text(
        "Choose what to quiz on:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return SELECTING_CONTENT


async def quiz_content_selected(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle content type selection and start the quiz."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return ConversationHandler.END

    await query.answer()

    if query.data == "quiz_cancel":
        await query.edit_message_text("Quiz cancelled. Use /quiz to try again!")
        return ConversationHandler.END

    # Parse content type
    content_mapping = {
        "quiz_content_hiragana": (ServiceContentType.HIRAGANA, ContentType.HIRAGANA),
        "quiz_content_katakana": (ServiceContentType.KATAKANA, ContentType.KATAKANA),
    }

    content_data = content_mapping.get(query.data)
    if not content_data:
        await query.edit_message_text("Invalid content type. Use /quiz to start again.")
        return ConversationHandler.END

    service_content_type, db_content_type = content_data
    user_id = update.effective_user.id

    # Get stored mode and difficulty
    mode = context.user_data.get("quiz_mode")
    difficulty = context.user_data.get("quiz_difficulty")

    if not mode or not difficulty:
        await query.edit_message_text("Session expired. Use /quiz to start again.")
        return ConversationHandler.END

    # Create quiz session
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)
        quiz_service = QuizService(content_service)

        # Get learned character IDs
        learned_ids = await progress_service.get_learned_character_ids(
            user_id, db_content_type
        )

        # Create quiz session
        quiz_session = await quiz_service.create_quiz_session(
            mode=mode,
            difficulty=difficulty,
            content_type=service_content_type,
            question_count=10,
            learned_character_ids=list(learned_ids) if learned_ids else None,
        )

        if not quiz_session:
            await query.edit_message_text(
                "❌ Not enough content available for this quiz. Try learning some characters first with /lesson!"
            )
            return ConversationHandler.END

        # Store quiz session in context
        context.user_data["quiz_session"] = quiz_session

        # Show first question
        return await show_question(query, context, quiz_session)


async def show_question(
    query, context: ContextTypes.DEFAULT_TYPE, quiz_session: QuizSession
) -> int:
    """Display the current quiz question."""
    quiz_service = QuizService(None)  # Content service not needed for this operation
    current_question = await quiz_service.get_current_question(quiz_session)

    if not current_question:
        # Quiz complete
        return await show_quiz_results(query, context, quiz_session)

    # Build question message
    question_num = quiz_session.current_question_index + 1
    total = len(quiz_session.questions)

    message_lines = [
        f"**Question {question_num}/{total}**",
        "",
        current_question.prompt,
        "",
    ]

    # Different keyboard based on mode
    if (
        current_question.mode == QuizMode.MULTIPLE_CHOICE
        or current_question.mode == QuizMode.RECOGNITION
    ):
        # Show options as buttons
        if current_question.options:
            keyboard = []
            for option in current_question.options:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            option, callback_data=f"quiz_answer_{option}"
                        )
                    ]
                )

            # Add hint and skip buttons
            if current_question.hints:
                keyboard.append(
                    [InlineKeyboardButton("💡 Hint", callback_data="quiz_hint")]
                )
            keyboard.append([InlineKeyboardButton("⏭️ Skip", callback_data="quiz_skip")])

            await query.edit_message_text(
                "\n".join(message_lines),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
    else:
        # Typing mode - wait for text input
        message_lines.append("Type your answer below:")

        # Add hint option
        keyboard = []
        if current_question.hints:
            keyboard.append(
                [InlineKeyboardButton("💡 Hint", callback_data="quiz_hint")]
            )
        keyboard.append([InlineKeyboardButton("⏭️ Skip", callback_data="quiz_skip")])

        await query.edit_message_text(
            "\n".join(message_lines),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    return ANSWERING


async def handle_quiz_answer_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle answer selection via button."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    # Handle special actions
    if query.data == "quiz_hint":
        return await show_hint(query, context)
    elif query.data == "quiz_skip":
        return await skip_question(query, context)

    # Parse answer
    if not query.data.startswith("quiz_answer_"):
        return ANSWERING

    user_answer = query.data.replace("quiz_answer_", "")

    # Process answer
    return await process_answer(query, context, user_answer)


async def handle_quiz_answer_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle typed answer."""
    if not update.message or not update.message.text:
        return ANSWERING

    user_answer = update.message.text.strip()

    # Create a mock query object for process_answer
    class MockQuery:
        def __init__(self, message):
            self.message = message

        async def edit_message_text(self, *args, **kwargs):
            await self.message.reply_text(*args, **kwargs)

    mock_query = MockQuery(update.message)

    return await process_answer(mock_query, context, user_answer)


async def process_answer(
    query, context: ContextTypes.DEFAULT_TYPE, user_answer: str
) -> int:
    """Process the user's answer."""
    quiz_session: Optional[QuizSession] = context.user_data.get("quiz_session")

    if not quiz_session:
        await query.edit_message_text("Session expired. Use /quiz to start again.")
        return ConversationHandler.END

    # Submit answer
    content_service = ContentService()
    await content_service.initialize()
    quiz_service = QuizService(content_service)

    is_correct, feedback, explanation = await quiz_service.submit_answer(
        quiz_session, user_answer
    )

    # Build result message
    result_lines = [feedback, ""]
    if explanation:
        result_lines.append(explanation)
        result_lines.append("")

    # Show progress
    result_lines.append(
        f"Progress: {quiz_session.correct_answers}/{quiz_session.total_attempts} correct"
    )

    # Next button
    keyboard = [[InlineKeyboardButton("➡️ Next Question", callback_data="quiz_next")]]

    await query.edit_message_text(
        "\n".join(result_lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return SHOW_RESULT


async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Advance to the next question."""
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()

    quiz_session: Optional[QuizSession] = context.user_data.get("quiz_session")

    if not quiz_session:
        await query.edit_message_text("Session expired. Use /quiz to start again.")
        return ConversationHandler.END

    # Advance quiz
    content_service = ContentService()
    await content_service.initialize()
    quiz_service = QuizService(content_service)

    has_more = await quiz_service.advance_to_next_question(quiz_session)

    if has_more:
        return await show_question(query, context, quiz_session)
    else:
        return await show_quiz_results(query, context, quiz_session)


async def show_hint(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a hint for the current question."""
    quiz_session: Optional[QuizSession] = context.user_data.get("quiz_session")

    if not quiz_session:
        await query.edit_message_text("Session expired. Use /quiz to start again.")
        return ConversationHandler.END

    content_service = ContentService()
    await content_service.initialize()
    quiz_service = QuizService(content_service)

    hint = await quiz_service.get_hint(quiz_session)

    if hint:
        await query.answer(f"💡 Hint: {hint}", show_alert=True)
    else:
        await query.answer("No hints available for this question.", show_alert=True)

    return ANSWERING


async def skip_question(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip the current question."""
    quiz_session: Optional[QuizSession] = context.user_data.get("quiz_session")

    if not quiz_session:
        await query.edit_message_text("Session expired. Use /quiz to start again.")
        return ConversationHandler.END

    # Record as incorrect
    content_service = ContentService()
    await content_service.initialize()
    quiz_service = QuizService(content_service)

    current_question = await quiz_service.get_current_question(quiz_session)
    if current_question:
        _, feedback, explanation = await quiz_service.submit_answer(
            quiz_session, "___SKIPPED___"
        )

        # Show the correct answer
        message_lines = [
            "⏭️ **Question Skipped**",
            "",
            f"The correct answer was: **{current_question.correct_answer}**",
            "",
        ]

        if explanation:
            message_lines.append(explanation)
            message_lines.append("")

        message_lines.append(
            f"Progress: {quiz_session.correct_answers}/{quiz_session.total_attempts} correct"
        )

        keyboard = [
            [InlineKeyboardButton("➡️ Next Question", callback_data="quiz_next")]
        ]

        await query.edit_message_text(
            "\n".join(message_lines),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

        return SHOW_RESULT

    return ANSWERING


async def show_quiz_results(
    query, context: ContextTypes.DEFAULT_TYPE, quiz_session: QuizSession
) -> int:
    """Display final quiz results."""
    content_service = ContentService()
    await content_service.initialize()
    quiz_service = QuizService(content_service)

    summary = await quiz_service.complete_quiz(quiz_session)

    # Build results message
    result_lines = [
        "🎊 **Quiz Complete!**",
        "",
        f"**Mode**: {summary['quiz_mode'].replace('_', ' ').title()}",
        f"**Difficulty**: {summary['difficulty'].title()}",
        f"**Content**: {summary['content_type'].title()}",
        "",
        f"**Score**: {summary['correct_answers']}/{summary['total_questions']}",
        f"**Accuracy**: {summary['accuracy']}%",
        f"**Time**: {summary['duration_seconds']} seconds",
        "",
        f"**Performance**: {summary['performance']}",
    ]

    # Show incorrectly answered questions
    if summary["answered_incorrectly"]:
        result_lines.append("")
        result_lines.append("**Review these:**")
        for ans in summary["answered_incorrectly"][:5]:  # Show max 5
            result_lines.append(f"• {ans['user_answer']} → {ans['correct_answer']}")

    result_lines.append("")
    result_lines.append("Use /quiz to try again or /lesson to learn more!")

    await query.edit_message_text("\n".join(result_lines), parse_mode="Markdown")

    # Clear session data
    context.user_data.pop("quiz_session", None)
    context.user_data.pop("quiz_mode", None)
    context.user_data.pop("quiz_difficulty", None)

    return ConversationHandler.END


async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the quiz."""
    if update.message:
        await update.message.reply_text(
            "Quiz cancelled. Use /quiz to start a new one anytime!"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "Quiz cancelled. Use /quiz to start a new one anytime!"
        )

    # Clear session data
    context.user_data.pop("quiz_session", None)
    context.user_data.pop("quiz_mode", None)
    context.user_data.pop("quiz_difficulty", None)

    return ConversationHandler.END
