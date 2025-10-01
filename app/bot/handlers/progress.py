"""
Progress tracking and statistics handlers for the Japanese Learning Telegram Bot.

This module provides commands to view learning progress, statistics,
and achievements using the spaced repetition progress tracking system.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import DatabaseManager
from app.models.user import User
from app.models.progress import ContentType
from app.services.progress_service import ProgressService
from app.services.content_service import ContentService

# Configure logging
logger = logging.getLogger(__name__)


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /progress command - show user's overall learning progress.

    Displays comprehensive progress statistics including items learned,
    mastered, accuracy, and review schedule.
    """
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id

    # Get database session and services
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        # Get user data
        user = await session.get(User, user_id)

        if not user:
            await update.message.reply_text(
                "User not found. Please use /start to register first."
            )
            return

        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        # Get overall statistics
        overall_stats = await progress_service.get_learning_statistics(user_id)

        # Get stats by content type
        content_stats = {}
        for content_type in ContentType:
            stats = await progress_service.get_learning_statistics(
                user_id, content_type
            )
            if stats["total_items"] > 0:
                content_stats[content_type.value] = stats

        # Build progress message
        message_lines = [
            f"📊 **Your Learning Progress**",
            f"",
            f"**👤 {user.display_name}**",
            f"Level: {user.current_level.value.title()}",
            f"Streak: {user.current_streak} days 🔥",
            f"",
            f"**📚 Overall Statistics:**",
            f"• Total Items: {overall_stats['total_items']}",
            f"• Learned: {overall_stats['learned_items']} ({overall_stats['learning_percentage']:.1f}%)",
            f"• Mastered: {overall_stats['mastered_items']} ({overall_stats['mastery_percentage']:.1f}%)",
            f"• Accuracy: {overall_stats['overall_accuracy']:.1f}%",
            f"",
        ]

        # Add review information
        if overall_stats["reviews_due_now"] > 0:
            message_lines.extend(
                [
                    f"⏰ **Reviews Due:**",
                    f"• Ready now: {overall_stats['reviews_due_now']}",
                    f"• Due today: {overall_stats['reviews_due_today']}",
                    f"",
                    f"Use /review to start reviewing!",
                    f"",
                ]
            )

        # Add content-specific breakdown
        if content_stats:
            message_lines.append("**📖 Progress by Content:**")

            emoji_map = {
                "hiragana": "あ",
                "katakana": "ア",
                "kanji": "漢",
                "vocabulary": "📖",
                "grammar": "📝",
            }

            for content_type, stats in content_stats.items():
                emoji = emoji_map.get(content_type, "📚")
                message_lines.append(
                    f"{emoji} **{content_type.title()}:** "
                    f"{stats['learned_items']}/{stats['total_items']} learned "
                    f"({stats['learning_percentage']:.0f}%)"
                )

            message_lines.append("")

        # Add study time
        study_hours = overall_stats["total_study_time_hours"]
        if study_hours > 0:
            message_lines.extend([f"⏱️ **Study Time:** {study_hours:.1f} hours", f""])

        # Add motivational message
        learning_pct = overall_stats["learning_percentage"]
        if learning_pct == 0:
            message_lines.append("🌱 Start your learning journey with /lesson!")
        elif learning_pct < 25:
            message_lines.append("🌿 Great start! Keep going!")
        elif learning_pct < 50:
            message_lines.append("🌳 You're making excellent progress!")
        elif learning_pct < 75:
            message_lines.append("🎋 More than halfway there! がんばって!")
        elif learning_pct < 100:
            message_lines.append("🌸 Almost there! You're doing amazing!")
        else:
            message_lines.append("🏆 Incredible! You've learned everything!")

        await update.message.reply_text("\n".join(message_lines), parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /stats command - show detailed statistics.

    Provides in-depth statistics including difficulty distribution,
    learning trends, and performance metrics.
    """
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id

    # Get database session and services
    db_manager = DatabaseManager()
    async with db_manager.get_session() as session:
        content_service = ContentService()
        await content_service.initialize()

        progress_service = ProgressService(session, content_service)

        # Get statistics
        stats = await progress_service.get_learning_statistics(user_id)

        if stats["total_items"] == 0:
            await update.message.reply_text(
                "No learning data yet. Start with /lesson to begin!"
            )
            return

        # Build detailed statistics message
        message_lines = [
            f"📈 **Detailed Learning Statistics**",
            f"",
            f"**📚 Learning Progress:**",
            f"• Total Items: {stats['total_items']}",
            f"• Items Learned: {stats['learned_items']} ({stats['learning_percentage']:.1f}%)",
            f"• Items Mastered: {stats['mastered_items']} ({stats['mastery_percentage']:.1f}%)",
            f"",
            f"**🎯 Performance:**",
            f"• Total Attempts: {stats['total_attempts']}",
            f"• Correct Answers: {stats['correct_attempts']}",
            f"• Overall Accuracy: {stats['overall_accuracy']:.1f}%",
            f"",
            f"**⏰ Review Schedule:**",
            f"• Due Now: {stats['reviews_due_now']}",
            f"• Due Today: {stats['reviews_due_today']}",
            f"",
        ]

        # Add difficulty distribution
        diff_dist = stats.get("difficulty_distribution", {})
        if any(count > 0 for count in diff_dist.values()):
            message_lines.append("**📊 Difficulty Distribution:**")

            diff_labels = {
                "very_easy": "⭐ Very Easy",
                "easy": "✅ Easy",
                "normal": "➖ Normal",
                "hard": "⚠️ Hard",
                "very_hard": "🔴 Very Hard",
            }

            for diff_key, label in diff_labels.items():
                count = diff_dist.get(diff_key, 0)
                if count > 0:
                    percentage = count / stats["total_items"] * 100
                    bar_length = int(percentage / 5)  # 20 max chars
                    bar = "▰" * bar_length + "▱" * (20 - bar_length)
                    message_lines.append(f"{label}: {bar} {count} ({percentage:.0f}%)")

            message_lines.append("")

        # Add study time
        if stats["total_study_time_hours"] > 0:
            message_lines.extend(
                [
                    f"⏱️ **Study Time:**",
                    f"• Total: {stats['total_study_time_hours']:.1f} hours",
                    f"• Average: {stats['total_study_time_hours'] / max(1, stats['total_attempts'] / 10):.1f} hours per 10 reviews",
                    f"",
                ]
            )

        # Add recommendations
        message_lines.append("**💡 Recommendations:**")

        if stats["reviews_due_now"] > 10:
            message_lines.append("• You have many reviews due - do /review soon!")
        elif stats["reviews_due_now"] > 0:
            message_lines.append("• Some reviews are ready - use /review when you can!")

        if stats["overall_accuracy"] < 70:
            message_lines.append("• Focus on reviewing to improve retention!")
        elif stats["overall_accuracy"] > 90:
            message_lines.append(
                "• Excellent accuracy! Consider learning new content with /lesson!"
            )

        very_hard_count = diff_dist.get("very_hard", 0) + diff_dist.get("hard", 0)
        if very_hard_count > 5:
            message_lines.append(
                f"• You have {very_hard_count} difficult items - review them frequently!"
            )

        await update.message.reply_text("\n".join(message_lines), parse_mode="Markdown")


async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /streak command - show learning streak information.

    Displays current streak, longest streak, and streak milestones.
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

        current_streak = user.current_streak
        longest_streak = user.longest_streak

        # Build streak message
        message_lines = [
            f"🔥 **Learning Streak**",
            f"",
            f"**Current Streak:** {current_streak} days",
            f"**Longest Streak:** {longest_streak} days",
            f"",
        ]

        # Add streak status
        if current_streak == 0:
            message_lines.append("Start your streak today with /lesson or /review!")
        elif current_streak < 7:
            message_lines.append(f"🌱 {7 - current_streak} more days to reach a week!")
        elif current_streak < 30:
            message_lines.append(
                f"🌿 Great progress! {30 - current_streak} more days to reach a month!"
            )
        elif current_streak < 100:
            message_lines.append(
                f"🌳 Amazing dedication! {100 - current_streak} more days to reach 100!"
            )
        else:
            message_lines.append(
                f"🏆 Incredible! You've maintained a {current_streak}-day streak!"
            )

        message_lines.append("")

        # Add motivation
        if current_streak >= longest_streak and current_streak > 0:
            message_lines.append("⭐ This is your longest streak ever! Keep it up!")

        message_lines.extend(
            [
                "",
                "**💡 Tip:** Study a little every day to maintain your streak!",
                "Use /reminders to set up daily notifications.",
            ]
        )

        await update.message.reply_text("\n".join(message_lines), parse_mode="Markdown")
