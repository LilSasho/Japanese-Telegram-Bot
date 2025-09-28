#!/usr/bin/env python3
"""
Demo script showcasing the Japanese Learning Content System

This demonstrates how the content service loads and serves hiragana characters
for different difficulty levels and learning progressions.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.content_service import ContentService, ContentType


async def demo_hiragana_learning():
    """Demonstrate the hiragana learning content system."""

    print("🇯🇵 Japanese Learning Content System Demo")
    print("=" * 50)

    # Initialize content service
    service = ContentService()

    # Demo 1: Learning progression by difficulty
    print("\n📚 LEARNING PROGRESSION BY DIFFICULTY")
    print("-" * 40)

    for difficulty in [1, 2, 3]:
        characters = await service.get_characters_by_difficulty(
            difficulty, ContentType.HIRAGANA, limit=5
        )

        if characters:
            char_display = " ".join([f"{c.character}({c.romaji})" for c in characters])
            difficulty_name = {1: "Vowels", 2: "K-row", 3: "S-row"}[difficulty]
            print(f"  Difficulty {difficulty} ({difficulty_name}): {char_display}")

    # Demo 2: Character details with learning aids
    print("\n🔍 CHARACTER LEARNING DETAILS")
    print("-" * 40)

    # Get first character from each difficulty
    sample_chars = []
    for diff in [1, 2, 3]:
        chars = await service.get_characters_by_difficulty(diff, ContentType.HIRAGANA, limit=1)
        if chars:
            sample_chars.append(chars[0])

    for char in sample_chars:
        print(f"\n  📝 {char.character} ({char.romaji})")
        print(f"     Pronunciation: {char.pronunciation}")
        print(f"     Meaning: {char.meaning}")
        print(f"     Mnemonic: {char.mnemonics}")
        if char.examples:
            example = char.examples[0]
            print(f"     Example: {example.word} ({example.romaji}) = {example.meaning}")

    # Demo 3: Content statistics and search
    print("\n📊 CONTENT STATISTICS")
    print("-" * 40)

    stats = await service.get_content_statistics()
    print(f"  Total content loaded: {stats}")

    # Test search functionality
    print("\n🔍 SEARCH FUNCTIONALITY")
    print("-" * 40)

    # Note: search_characters requires ContentSearchFilter - simplified demo
    print("  Search functionality available via ContentSearchFilter")

    # Demo 4: Learning metadata
    print("\n📊 LEARNING PROGRESSION METADATA")
    print("-" * 40)

    from app.services.content_service import ContentCategory

    # Get learning progression for hiragana basic
    progression = await service.get_learning_progression(ContentCategory.HIRAGANA_BASIC)

    # Get next characters to learn
    next_chars = await service.get_next_characters_to_learn(ContentCategory.HIRAGANA_BASIC, 3)

    if progression:
        print(f"  Learning progression available for hiragana")

    if next_chars:
        char_list = [f"{c.character}({c.romaji})" for c in next_chars]
        print(f"  Next characters to learn: {' '.join(char_list)}")

    # Demo 5: Simulate lesson creation
    print("\n🎓 SIMULATED LESSON CREATION")
    print("-" * 40)

    print("  Creating beginner lesson with first 5 characters...")
    lesson_chars = await service.get_characters_by_difficulty(1, ContentType.HIRAGANA, limit=5)

    if lesson_chars:
        print("  ✅ Lesson Content Generated:")
        for i, char in enumerate(lesson_chars, 1):
            print(f"     {i}. {char.character} = {char.romaji} ({char.pronunciation})")

    print("\n✨ Content system demo complete!")
    print("🚀 Ready for integration with Telegram bot and spaced repetition!")


async def demo_error_handling():
    """Demonstrate error handling in content service."""

    print("\n🛡️  ERROR HANDLING DEMO")
    print("-" * 40)

    service = ContentService()

    try:
        # Try to load non-existent content
        await service.load_content(ContentType.HIRAGANA, 'nonexistent')
    except Exception as e:
        print(f"  ✅ Proper error handling: {type(e).__name__}")

    # Test with invalid difficulty
    try:
        chars = await service.get_characters_by_difficulty(99, ContentType.HIRAGANA)
        print(f"  ✅ Graceful handling of invalid difficulty: {len(chars)} results")
    except Exception as e:
        print(f"  ✅ Error handling: {e}")


if __name__ == "__main__":
    print("Starting Japanese Learning Content System Demo...")

    try:
        asyncio.run(demo_hiragana_learning())
        asyncio.run(demo_error_handling())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure you're running from the project root with venv activated")