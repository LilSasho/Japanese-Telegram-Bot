"""
Content models for the Japanese Learning Telegram Bot.

This module defines models for storing Japanese learning content
including characters, vocabulary, and related metadata.
"""

from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import String, Text, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CharacterType(str, Enum):
    """Types of Japanese characters."""

    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    KANJI = "kanji"


class JapaneseCharacter(Base):
    """Model for Japanese characters (hiragana, katakana, kanji)."""

    __tablename__ = "japanese_characters"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )  # e.g., "hiragana_a", "kanji_水"

    # Character information
    character: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # The actual character
    character_type: Mapped[CharacterType] = mapped_column(String(20), nullable=False)

    # Pronunciations
    romaji: Mapped[str] = mapped_column(String(50), nullable=False)
    hiragana_reading: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # For kanji
    katakana_reading: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # For kanji

    # Meanings and translations
    meanings: Mapped[List[str]] = mapped_column(
        JSON, nullable=False
    )  # List of English meanings

    # Learning metadata
    difficulty_level: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # 1-5
    frequency_rank: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Usage frequency
    jlpt_level: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # JLPT level (5-1)

    # Kanji-specific data
    stroke_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    radical: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    kun_readings: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    on_readings: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Learning aids
    mnemonics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_words: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    cultural_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        """String representation of the character."""
        return f"<JapaneseCharacter(id={self.id}, character={self.character})>"

    @property
    def display_name(self) -> str:
        """Get display name for the character."""
        return f"{self.character} ({self.romaji})"

    @property
    def reading_info(self) -> str:
        """Get formatted reading information."""
        if self.character_type == CharacterType.KANJI:
            readings = []
            if self.kun_readings:
                readings.append(f"Kun: {', '.join(self.kun_readings)}")
            if self.on_readings:
                readings.append(f"On: {', '.join(self.on_readings)}")
            return " | ".join(readings) if readings else self.romaji
        return self.romaji

    def get_example_words(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get example words containing this character.

        Args:
            limit: Maximum number of examples to return

        Returns:
            List of example word dictionaries
        """
        if not self.example_words:
            return []
        return self.example_words[:limit]


class Vocabulary(Base):
    """Model for Japanese vocabulary words."""

    __tablename__ = "vocabulary"

    # Primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "vocab_hello"

    # Word information
    word: Mapped[str] = mapped_column(String(100), nullable=False)  # Japanese word
    reading: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Hiragana reading
    romaji: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Romanized reading

    # Meanings and translations
    meanings: Mapped[List[str]] = mapped_column(
        JSON, nullable=False
    )  # English meanings
    part_of_speech: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # noun, verb, etc.

    # Learning metadata
    difficulty_level: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # 1-5
    frequency_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jlpt_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Context and usage
    example_sentences: Mapped[Optional[List[Dict[str, str]]]] = mapped_column(
        JSON, nullable=True
    )
    usage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    formality_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # casual, polite, formal

    # Related information
    kanji_components: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    related_words: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    antonyms: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    synonyms: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        """String representation of the vocabulary item."""
        return f"<Vocabulary(id={self.id}, word={self.word})>"

    @property
    def display_name(self) -> str:
        """Get display name for the vocabulary item."""
        return f"{self.word} ({self.reading})"

    @property
    def primary_meaning(self) -> str:
        """Get the primary (first) meaning."""
        return self.meanings[0] if self.meanings else "No meaning available"

    def get_example_sentences(self, limit: int = 2) -> List[Dict[str, str]]:
        """Get example sentences for this vocabulary.

        Args:
            limit: Maximum number of examples to return

        Returns:
            List of example sentence dictionaries
        """
        if not self.example_sentences:
            return []
        return self.example_sentences[:limit]
