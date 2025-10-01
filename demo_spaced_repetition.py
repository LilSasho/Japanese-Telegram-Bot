#!/usr/bin/env python3
"""
Demonstration script for the SM-2 Spaced Repetition Algorithm.

This script simulates learning Japanese characters using the SM-2 algorithm,
showing how review intervals adapt based on user performance.
"""

import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Tuple

from app.utils.spaced_repetition import (
    SpacedRepetitionSM2,
    QualityRating,
    ReviewResult,
    calculate_review,
)


def print_separator(char: str = "=", length: int = 70):
    """Print a separator line."""
    print(char * length)


def print_review_result(character: str, review: ReviewResult, attempt: int):
    """Print formatted review result."""
    print(f"\n📝 Review #{attempt}: {character}")
    print(f"   Quality Rating: {review.quality_rating} ({QualityRating(review.quality_rating).name})")
    print(f"   Easiness Factor: {float(review.easiness_factor):.2f}")
    print(f"   Repetition Count: {review.repetition_count}")
    print(f"   Next Review: {review.interval_days} days")
    print(f"   Next Review Date: {review.next_review_date.strftime('%Y-%m-%d')}")


def simulate_learning_progression():
    """Simulate a learning progression with varying quality ratings."""
    print_separator()
    print("🎯 SM-2 SPACED REPETITION DEMONSTRATION")
    print_separator()
    print()

    # Character to learn
    character = "あ (a - hiragana vowel)"
    print(f"Learning: {character}")
    print()

    # Initialize SM-2
    sm2 = SpacedRepetitionSM2()

    # Simulate learning sessions with different quality ratings
    learning_sessions = [
        (QualityRating.CORRECT_HESITATION, "First exposure - correct but slow"),
        (QualityRating.CORRECT_HESITATION, "Second review - still hesitant"),
        (QualityRating.PERFECT, "Getting better - perfect recall!"),
        (QualityRating.PERFECT, "Strong memory now"),
        (QualityRating.CORRECT_DIFFICULT, "Some difficulty after longer interval"),
        (QualityRating.PERFECT, "Back on track"),
        (QualityRating.PERFECT, "Confident now"),
    ]

    # Track progression
    current_easiness = Decimal("2.5")
    current_repetitions = 0
    current_interval = 1
    last_review = datetime.now(timezone.utc)

    print_separator("-")
    print("Learning Progression:")
    print_separator("-")

    for attempt, (quality, description) in enumerate(learning_sessions, 1):
        print(f"\n{'='*70}")
        print(f"Session {attempt}: {description}")
        print(f"{'='*70}")

        # Calculate next review
        result = sm2.calculate_next_review(
            quality=quality,
            current_easiness=current_easiness,
            current_repetitions=current_repetitions,
            current_interval=current_interval,
            last_review_date=last_review,
        )

        # Print result
        print_review_result(character, result, attempt)

        # Update for next iteration
        current_easiness = result.easiness_factor
        current_repetitions = result.repetition_count
        current_interval = result.interval_days
        last_review = result.next_review_date

    print()
    print_separator()
    print("✅ Demonstration Complete!")
    print()


def compare_quality_ratings():
    """Compare how different quality ratings affect intervals."""
    print_separator()
    print("📊 QUALITY RATING COMPARISON")
    print_separator()
    print()
    print("Starting with: EF=2.5, Repetitions=2, Interval=6 days")
    print()

    # Common starting point
    base_easiness = Decimal("2.5")
    base_repetitions = 2
    base_interval = 6

    print(f"{'Quality Rating':<20} {'Description':<25} {'New EF':<10} {'Reps':<8} {'Interval':<10}")
    print(f"{'-'*20} {'-'*25} {'-'*10} {'-'*8} {'-'*10}")

    # Test each quality rating
    for quality in range(6):
        result = calculate_review(
            quality=quality,
            easiness=base_easiness,
            repetitions=base_repetitions,
            interval=base_interval,
        )

        quality_name = QualityRating(quality).name
        print(
            f"{quality:<20} {quality_name:<25} "
            f"{float(result.easiness_factor):<10.2f} "
            f"{result.repetition_count:<8} "
            f"{result.interval_days:<10} days"
        )

    print()
    print_separator()


def demonstrate_binary_conversion():
    """Demonstrate binary (correct/incorrect) to quality conversion."""
    print_separator()
    print("🔄 BINARY TO QUALITY CONVERSION")
    print_separator()
    print()
    print("For systems that only track correct/incorrect:")
    print()

    sm2 = SpacedRepetitionSM2()

    test_cases = [
        (False, None, "Incorrect answer"),
        (True, None, "Correct (no time data)"),
        (True, 1500, "Correct - very fast (1.5s)"),
        (True, 3000, "Correct - medium (3s)"),
        (True, 5000, "Correct - slow (5s)"),
    ]

    print(f"{'Result':<10} {'Time (ms)':<12} {'Description':<30} {'Quality':<10} {'Rating Name':<20}")
    print(f"{'-'*10} {'-'*12} {'-'*30} {'-'*10} {'-'*20}")

    for is_correct, time_ms, description in test_cases:
        quality = sm2.convert_binary_to_quality(is_correct, time_ms)
        result_str = "✅ Correct" if is_correct else "❌ Incorrect"
        time_str = f"{time_ms}" if time_ms else "N/A"

        print(
            f"{result_str:<10} {time_str:<12} {description:<30} "
            f"{int(quality):<10} {quality.name:<20}"
        )

    print()
    print_separator()


def demonstrate_failed_review():
    """Demonstrate what happens with failed reviews."""
    print_separator()
    print("❌ FAILED REVIEW DEMONSTRATION")
    print_separator()
    print()

    print("Learning character: か (ka)")
    print("Scenario: User was progressing well, then failed a review")
    print()

    # Start with good progress
    easiness = Decimal("2.6")
    repetitions = 4
    interval = 15

    print(f"Current state: EF={float(easiness):.2f}, Reps={repetitions}, Interval={interval} days")
    print()

    # Failed review
    print("User fails the review (Quality = 2: Incorrect but remembered)...")
    result = calculate_review(
        quality=QualityRating.INCORRECT_REMEMBERED,
        easiness=easiness,
        repetitions=repetitions,
        interval=interval,
    )

    print()
    print("After failed review:")
    print(f"   New Easiness Factor: {float(result.easiness_factor):.2f} (decreased)")
    print(f"   Repetition Count: {result.repetition_count} (reset to 0)")
    print(f"   Next Interval: {result.interval_days} day (restart)")
    print()
    print("💡 The algorithm resets progress but remembers the difficulty (lower EF)")
    print("   This means future intervals will grow more slowly for this item.")
    print()
    print_separator()


async def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "Japanese Learning Bot - SM-2 Algorithm Demo" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Run demonstrations
    simulate_learning_progression()
    print("\n")

    compare_quality_ratings()
    print("\n")

    demonstrate_binary_conversion()
    print("\n")

    demonstrate_failed_review()

    print()
    print("="*70)
    print("🎓 Key Takeaways:")
    print("="*70)
    print("1. Higher quality ratings = longer intervals (better memory)")
    print("2. Failed reviews reset the learning process but adjust difficulty")
    print("3. Easiness factor adapts to individual item difficulty")
    print("4. Binary correct/incorrect can be converted to quality ratings")
    print("5. The algorithm optimizes review timing for long-term retention")
    print("="*70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
