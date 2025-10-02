"""
Content service for the Japanese Learning Telegram Bot.

This module provides comprehensive content management functionality including:
- Loading JSON content files from data/content/ directory
- Character retrieval by difficulty, category, or ID
- Advanced filtering and searching capabilities
- Async patterns consistent with SQLAlchemy and telegram-bot frameworks
- Error handling and logging
- Integration with spaced repetition algorithms
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import fnmatch

from app.core.config import Config


# Configure logging
logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categories of learning content."""

    HIRAGANA_BASIC = "hiragana_basic"
    HIRAGANA_COMBINATIONS = "hiragana_combinations"
    HIRAGANA_ADVANCED = "hiragana_advanced"
    KATAKANA_BASIC = "katakana_basic"
    KATAKANA_COMBINATIONS = "katakana_combinations"
    KATAKANA_ADVANCED = "katakana_advanced"
    KANJI_BASIC = "kanji_basic"
    KANJI_INTERMEDIATE = "kanji_intermediate"
    KANJI_ADVANCED = "kanji_advanced"
    VOCABULARY_BASIC = "vocabulary_basic"
    VOCABULARY_INTERMEDIATE = "vocabulary_intermediate"
    VOCABULARY_ADVANCED = "vocabulary_advanced"
    CULTURAL_NOTES = "cultural_notes"


class ContentType(Enum):
    """Types of learning content."""

    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    KANJI = "kanji"
    VOCABULARY = "vocabulary"
    CULTURAL = "cultural"


@dataclass
class CharacterExample:
    """Represents an example usage of a character."""

    word: str
    romaji: str
    meaning: str


@dataclass
class CharacterData:
    """Represents a Japanese character with all associated learning data."""

    id: str
    character: str
    romaji: str
    pronunciation: str
    meaning: Optional[str] = None
    difficulty: int = 1
    stroke_order: List[str] = None
    mnemonics: Optional[str] = None
    examples: List[CharacterExample] = None
    common_mistakes: List[str] = None
    tags: List[str] = None
    category: Optional[ContentCategory] = None
    content_type: Optional[ContentType] = None
    audio_file: Optional[str] = None
    stroke_count: Optional[int] = None
    frequency: Optional[int] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.stroke_order is None:
            self.stroke_order = []
        if self.examples is None:
            self.examples = []
        if self.common_mistakes is None:
            self.common_mistakes = []
        if self.tags is None:
            self.tags = []


@dataclass
class ContentMetadata:
    """Metadata for a content file."""

    name: str
    description: str
    difficulty: int
    total_characters: int
    category: str
    version: str


@dataclass
class LearningProgression:
    """Learning progression information."""

    suggested_order: List[str]
    difficulty_groups: Dict[str, List[str]]
    estimated_time: Optional[str] = None


@dataclass
class ContentFile:
    """Complete content file data structure."""

    metadata: ContentMetadata
    characters: List[CharacterData]
    learning_progression: Optional[LearningProgression] = None


class ContentSearchFilter:
    """Filter for searching content."""

    def __init__(
        self,
        content_types: Optional[List[ContentType]] = None,
        categories: Optional[List[ContentCategory]] = None,
        difficulty_range: Optional[Tuple[int, int]] = None,
        tags: Optional[List[str]] = None,
        character_pattern: Optional[str] = None,
        romaji_pattern: Optional[str] = None,
        meaning_pattern: Optional[str] = None,
        exclude_learned: bool = False,
        learned_character_ids: Optional[Set[str]] = None,
    ):
        self.content_types = content_types or []
        self.categories = categories or []
        self.difficulty_range = difficulty_range
        self.tags = tags or []
        self.character_pattern = character_pattern
        self.romaji_pattern = romaji_pattern
        self.meaning_pattern = meaning_pattern
        self.exclude_learned = exclude_learned
        self.learned_character_ids = learned_character_ids or set()


class ContentService:
    """Service for managing Japanese learning content."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the content service.

        Args:
            config: Configuration object. If None, creates default Config.
        """
        self.config = config or Config()
        self._content_cache: Dict[str, ContentFile] = {}
        self._character_index: Dict[str, CharacterData] = {}
        self._data_dir = Path("data/content")
        self._content_loaded = False
        self._load_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the content service by loading all content files."""
        async with self._load_lock:
            if not self._content_loaded:
                await self._load_all_content()
                self._build_character_index()
                self._content_loaded = True
                logger.info("Content service initialized successfully")

    async def _load_all_content(self) -> None:
        """Load all content files from the data directory."""
        if not self._data_dir.exists():
            logger.warning(f"Content directory {self._data_dir} does not exist")
            return

        content_files = []

        # Discover all JSON files in content directory
        for content_file in self._data_dir.rglob("*.json"):
            content_files.append(content_file)

        logger.info(f"Found {len(content_files)} content files to load")

        # Load files concurrently
        load_tasks = [self._load_content_file(file_path) for file_path in content_files]
        results = await asyncio.gather(*load_tasks, return_exceptions=True)

        # Process results
        loaded_count = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to load content file: {result}")
            elif result:
                loaded_count += 1

        logger.info(f"Successfully loaded {loaded_count} content files")

    async def _load_content_file(self, file_path: Path) -> bool:
        """
        Load a single content file.

        Args:
            file_path: Path to the JSON content file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            content_file = self._parse_content_file(data, file_path)
            if content_file:
                # Use file path as key for uniqueness
                key = str(file_path.relative_to(self._data_dir))
                self._content_cache[key] = content_file
                logger.debug(f"Loaded content file: {key}")
                return True
            else:
                logger.warning(f"Failed to parse content file: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error loading content file {file_path}: {e}")
            return False

    def _parse_content_file(
        self, data: Dict[str, Any], file_path: Path
    ) -> Optional[ContentFile]:
        """
        Parse JSON data into a ContentFile object.

        Args:
            data: JSON data
            file_path: Original file path for context

        Returns:
            ContentFile object or None if parsing fails
        """
        try:
            # Parse metadata
            metadata_data = data.get("metadata", {})
            metadata = ContentMetadata(
                name=metadata_data.get("name", file_path.stem),
                description=metadata_data.get("description", ""),
                difficulty=metadata_data.get("difficulty", 1),
                total_characters=metadata_data.get("total_characters", 0),
                category=metadata_data.get("category", "unknown"),
                version=metadata_data.get("version", "1.0"),
            )

            # Parse characters
            characters = []
            for char_data in data.get("characters", []):
                character = self._parse_character_data(char_data, file_path)
                if character:
                    characters.append(character)

            # Parse learning progression (optional)
            learning_progression = None
            if "learning_progression" in data:
                prog_data = data["learning_progression"]
                learning_progression = LearningProgression(
                    suggested_order=prog_data.get("suggested_order", []),
                    difficulty_groups=prog_data.get("difficulty_groups", {}),
                    estimated_time=prog_data.get("estimated_time"),
                )

            return ContentFile(
                metadata=metadata,
                characters=characters,
                learning_progression=learning_progression,
            )

        except Exception as e:
            logger.error(f"Error parsing content file {file_path}: {e}")
            return None

    def _parse_character_data(
        self, char_data: Dict[str, Any], file_path: Path
    ) -> Optional[CharacterData]:
        """
        Parse character data from JSON.

        Args:
            char_data: Character data from JSON
            file_path: Original file path for context

        Returns:
            CharacterData object or None if parsing fails
        """
        try:
            # Parse examples
            examples = []
            for example_data in char_data.get("examples", []):
                example = CharacterExample(
                    word=example_data.get("word", ""),
                    romaji=example_data.get("romaji", ""),
                    meaning=example_data.get("meaning", ""),
                )
                examples.append(example)

            # Determine content type and category from file path
            content_type = self._determine_content_type(file_path)
            category = self._determine_category(file_path, char_data)

            character = CharacterData(
                id=char_data.get("id", ""),
                character=char_data.get("character", ""),
                romaji=char_data.get("romaji", ""),
                pronunciation=char_data.get("pronunciation", ""),
                meaning=char_data.get("meaning"),
                difficulty=char_data.get("difficulty", 1),
                stroke_order=char_data.get("stroke_order", []),
                mnemonics=char_data.get("mnemonics"),
                examples=examples,
                common_mistakes=char_data.get("common_mistakes", []),
                tags=char_data.get("tags", []),
                category=category,
                content_type=content_type,
                audio_file=char_data.get("audio_file"),
                stroke_count=char_data.get("stroke_count"),
                frequency=char_data.get("frequency"),
            )

            return character

        except Exception as e:
            logger.error(f"Error parsing character data in {file_path}: {e}")
            return None

    def _determine_content_type(self, file_path: Path) -> Optional[ContentType]:
        """Determine content type from file path."""
        path_parts = file_path.parts
        for part in path_parts:
            part_lower = part.lower()
            if "hiragana" in part_lower:
                return ContentType.HIRAGANA
            elif "katakana" in part_lower:
                return ContentType.KATAKANA
            elif "kanji" in part_lower:
                return ContentType.KANJI
            elif "vocabulary" in part_lower:
                return ContentType.VOCABULARY
            elif "cultural" in part_lower:
                return ContentType.CULTURAL
        return None

    def _determine_category(
        self, file_path: Path, char_data: Dict[str, Any]
    ) -> Optional[ContentCategory]:
        """Determine content category from file path and character data."""
        path_str = str(file_path).lower()

        # Try to match known category patterns
        if "hiragana" in path_str:
            if "basic" in path_str:
                return ContentCategory.HIRAGANA_BASIC
            elif "combination" in path_str:
                return ContentCategory.HIRAGANA_COMBINATIONS
            elif "advanced" in path_str:
                return ContentCategory.HIRAGANA_ADVANCED
        elif "katakana" in path_str:
            if "basic" in path_str:
                return ContentCategory.KATAKANA_BASIC
            elif "combination" in path_str:
                return ContentCategory.KATAKANA_COMBINATIONS
            elif "advanced" in path_str:
                return ContentCategory.KATAKANA_ADVANCED
        elif "kanji" in path_str:
            if "basic" in path_str:
                return ContentCategory.KANJI_BASIC
            elif "intermediate" in path_str:
                return ContentCategory.KANJI_INTERMEDIATE
            elif "advanced" in path_str:
                return ContentCategory.KANJI_ADVANCED
        elif "vocabulary" in path_str:
            if "basic" in path_str:
                return ContentCategory.VOCABULARY_BASIC
            elif "intermediate" in path_str:
                return ContentCategory.VOCABULARY_INTERMEDIATE
            elif "advanced" in path_str:
                return ContentCategory.VOCABULARY_ADVANCED
        elif "cultural" in path_str:
            return ContentCategory.CULTURAL_NOTES

        return None

    def _build_character_index(self) -> None:
        """Build an index of all characters for fast lookup."""
        self._character_index.clear()

        for content_file in self._content_cache.values():
            for character in content_file.characters:
                if character.id:
                    self._character_index[character.id] = character

        logger.debug(
            f"Built character index with {len(self._character_index)} characters"
        )

    async def get_character_by_id(self, character_id: str) -> Optional[CharacterData]:
        """
        Get a character by its unique ID.

        Args:
            character_id: Unique character identifier

        Returns:
            CharacterData object or None if not found
        """
        await self._ensure_initialized()
        return self._character_index.get(character_id)

    async def get_characters_by_difficulty(
        self,
        difficulty: int,
        content_type: Optional[ContentType] = None,
        limit: Optional[int] = None,
    ) -> List[CharacterData]:
        """
        Get characters by difficulty level.

        Args:
            difficulty: Difficulty level (1-5)
            content_type: Optional content type filter
            limit: Maximum number of characters to return

        Returns:
            List of CharacterData objects
        """
        await self._ensure_initialized()

        characters = []
        for content_file in self._content_cache.values():
            for character in content_file.characters:
                if character.difficulty == difficulty:
                    if content_type is None or character.content_type == content_type:
                        characters.append(character)

        if limit:
            characters = characters[:limit]

        return characters

    async def get_characters_by_category(
        self, category: ContentCategory, limit: Optional[int] = None
    ) -> List[CharacterData]:
        """
        Get characters by content category.

        Args:
            category: Content category
            limit: Maximum number of characters to return

        Returns:
            List of CharacterData objects
        """
        await self._ensure_initialized()

        characters = []
        for content_file in self._content_cache.values():
            if content_file.metadata.category == category.value:
                characters.extend(content_file.characters)

        if limit:
            characters = characters[:limit]

        return characters

    async def search_characters(
        self, search_filter: ContentSearchFilter
    ) -> List[CharacterData]:
        """
        Search characters using advanced filtering.

        Args:
            search_filter: Search filter criteria

        Returns:
            List of matching CharacterData objects
        """
        await self._ensure_initialized()

        results = []

        for content_file in self._content_cache.values():
            for character in content_file.characters:
                if self._matches_filter(character, search_filter):
                    results.append(character)

        return results

    def _matches_filter(
        self, character: CharacterData, search_filter: ContentSearchFilter
    ) -> bool:
        """
        Check if a character matches the search filter.

        Args:
            character: Character to check
            search_filter: Filter criteria

        Returns:
            True if character matches all filter criteria
        """
        # Content type filter
        if (
            search_filter.content_types
            and character.content_type not in search_filter.content_types
        ):
            return False

        # Category filter
        if (
            search_filter.categories
            and character.category not in search_filter.categories
        ):
            return False

        # Difficulty range filter
        if search_filter.difficulty_range:
            min_diff, max_diff = search_filter.difficulty_range
            if not (min_diff <= character.difficulty <= max_diff):
                return False

        # Tags filter (character must have at least one matching tag)
        if search_filter.tags:
            if not any(tag in character.tags for tag in search_filter.tags):
                return False

        # Character pattern filter
        if search_filter.character_pattern:
            if not fnmatch.fnmatch(
                character.character, search_filter.character_pattern
            ):
                return False

        # Romaji pattern filter
        if search_filter.romaji_pattern:
            if not fnmatch.fnmatch(
                character.romaji.lower(), search_filter.romaji_pattern.lower()
            ):
                return False

        # Meaning pattern filter
        if search_filter.meaning_pattern and character.meaning:
            if not fnmatch.fnmatch(
                character.meaning.lower(), search_filter.meaning_pattern.lower()
            ):
                return False

        # Exclude learned characters
        if (
            search_filter.exclude_learned
            and character.id in search_filter.learned_character_ids
        ):
            return False

        return True

    async def get_learning_progression(
        self, category: ContentCategory
    ) -> Optional[LearningProgression]:
        """
        Get learning progression for a category.

        Args:
            category: Content category

        Returns:
            LearningProgression object or None if not found
        """
        await self._ensure_initialized()

        for content_file in self._content_cache.values():
            if content_file.metadata.category == category.value:
                return content_file.learning_progression

        return None

    async def get_suggested_characters_for_review(
        self,
        learned_characters: Set[str],
        review_count: int = 10,
        prefer_difficult: bool = True,
    ) -> List[CharacterData]:
        """
        Get suggested characters for spaced repetition review.

        Args:
            learned_characters: Set of character IDs the user has learned
            review_count: Number of characters to suggest
            prefer_difficult: Prioritize more difficult characters

        Returns:
            List of CharacterData objects for review
        """
        await self._ensure_initialized()

        # Get all learned characters
        review_candidates = []
        for char_id in learned_characters:
            character = await self.get_character_by_id(char_id)
            if character:
                review_candidates.append(character)

        # Sort by difficulty if preferred
        if prefer_difficult:
            review_candidates.sort(key=lambda x: x.difficulty, reverse=True)

        return review_candidates[:review_count]

    async def get_next_characters_to_learn(
        self, learned_characters: Set[str], content_type: ContentType, count: int = 5
    ) -> List[CharacterData]:
        """
        Get the next characters to learn based on learning progression.

        Args:
            learned_characters: Set of character IDs already learned
            content_type: Type of content to learn
            count: Number of characters to return

        Returns:
            List of CharacterData objects to learn next
        """
        await self._ensure_initialized()

        # Find content files for the specified type
        candidates = []

        for content_file in self._content_cache.values():
            if any(
                char.content_type == content_type for char in content_file.characters
            ):
                # Use learning progression if available
                if content_file.learning_progression:
                    suggested_order = content_file.learning_progression.suggested_order
                    for char_id in suggested_order:
                        if char_id not in learned_characters:
                            character = await self.get_character_by_id(char_id)
                            if character and character.content_type == content_type:
                                candidates.append(character)
                                if len(candidates) >= count:
                                    break
                else:
                    # Fall back to difficulty-based ordering
                    unlearned = [
                        char
                        for char in content_file.characters
                        if char.content_type == content_type
                        and char.id not in learned_characters
                    ]
                    unlearned.sort(key=lambda x: (x.difficulty, x.id))
                    candidates.extend(unlearned[:count])

        return candidates[:count]

    async def get_content_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded content.

        Returns:
            Dictionary containing content statistics
        """
        await self._ensure_initialized()

        stats = {
            "total_files": len(self._content_cache),
            "total_characters": len(self._character_index),
            "content_types": {},
            "categories": {},
            "difficulty_distribution": {},
        }

        # Count by content type and category
        for character in self._character_index.values():
            # Content type stats
            if character.content_type:
                content_type_name = character.content_type.value
                stats["content_types"][content_type_name] = (
                    stats["content_types"].get(content_type_name, 0) + 1
                )

            # Category stats
            if character.category:
                category_name = character.category.value
                stats["categories"][category_name] = (
                    stats["categories"].get(category_name, 0) + 1
                )

            # Difficulty stats
            difficulty = character.difficulty
            stats["difficulty_distribution"][difficulty] = (
                stats["difficulty_distribution"].get(difficulty, 0) + 1
            )

        return stats

    async def validate_content_integrity(self) -> Dict[str, List[str]]:
        """
        Validate the integrity of loaded content.

        Returns:
            Dictionary containing validation issues found
        """
        await self._ensure_initialized()

        issues = {
            "missing_ids": [],
            "duplicate_ids": [],
            "missing_characters": [],
            "missing_romaji": [],
            "invalid_difficulty": [],
            "missing_examples": [],
        }

        seen_ids = set()

        for content_file in self._content_cache.values():
            for character in content_file.characters:
                # Check for missing IDs
                if not character.id:
                    issues["missing_ids"].append(
                        f"Character '{character.character}' missing ID"
                    )

                # Check for duplicate IDs
                if character.id in seen_ids:
                    issues["duplicate_ids"].append(f"Duplicate ID: {character.id}")
                else:
                    seen_ids.add(character.id)

                # Check for missing character
                if not character.character:
                    issues["missing_characters"].append(
                        f"ID '{character.id}' missing character"
                    )

                # Check for missing romaji
                if not character.romaji:
                    issues["missing_romaji"].append(
                        f"Character '{character.character}' missing romaji"
                    )

                # Check difficulty range
                if not (1 <= character.difficulty <= 5):
                    issues["invalid_difficulty"].append(
                        f"Character '{character.character}' has invalid difficulty: {character.difficulty}"
                    )

                # Check for missing examples (warning for advanced content)
                if character.difficulty > 2 and not character.examples:
                    issues["missing_examples"].append(
                        f"Advanced character '{character.character}' has no examples"
                    )

        return issues

    async def reload_content(self) -> None:
        """Reload all content from disk."""
        async with self._load_lock:
            logger.info("Reloading content...")
            self._content_cache.clear()
            self._character_index.clear()
            self._content_loaded = False
            await self._load_all_content()
            self._build_character_index()
            self._content_loaded = True
            logger.info("Content reloaded successfully")

    async def _ensure_initialized(self) -> None:
        """Ensure the service is initialized."""
        if not self._content_loaded:
            await self.initialize()


# Convenience functions for common operations


async def create_difficulty_filter(
    min_difficulty: int = 1,
    max_difficulty: int = 5,
    content_type: Optional[ContentType] = None,
) -> ContentSearchFilter:
    """Create a filter for difficulty range."""
    return ContentSearchFilter(
        content_types=[content_type] if content_type else None,
        difficulty_range=(min_difficulty, max_difficulty),
    )


async def create_tag_filter(
    tags: List[str], content_type: Optional[ContentType] = None
) -> ContentSearchFilter:
    """Create a filter for specific tags."""
    return ContentSearchFilter(
        content_types=[content_type] if content_type else None, tags=tags
    )


async def create_learning_filter(
    learned_characters: Set[str], exclude_learned: bool = True
) -> ContentSearchFilter:
    """Create a filter that excludes or includes learned characters."""
    return ContentSearchFilter(
        exclude_learned=exclude_learned, learned_character_ids=learned_characters
    )
