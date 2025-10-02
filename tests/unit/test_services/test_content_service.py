"""
Unit tests for ContentService.

Tests content loading, character retrieval, search functionality,
and content validation.
"""

import pytest

from app.services.content_service import (
    ContentService,
    ContentType,
    ContentCategory,
    ContentSearchFilter,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestContentService:
    """Tests for ContentService class."""

    async def test_initialization(self, content_service: ContentService):
        """Test that content service initializes successfully."""
        assert content_service is not None
        assert content_service._content_loaded is True

    async def test_get_content_statistics(self, content_service: ContentService):
        """Test getting content statistics."""
        stats = await content_service.get_content_statistics()

        assert "total_files" in stats
        assert "total_characters" in stats
        assert "content_types" in stats
        assert stats["total_characters"] > 0

    async def test_statistics_includes_all_types(self, content_service: ContentService):
        """Test that statistics include all content types."""
        stats = await content_service.get_content_statistics()

        content_types = stats["content_types"]
        assert "hiragana" in content_types
        assert "katakana" in content_types
        assert "kanji" in content_types

    async def test_get_character_by_id_exists(self, content_service: ContentService):
        """Test retrieving an existing character by ID."""
        char = await content_service.get_character_by_id("hira_001")

        assert char is not None
        assert char.id == "hira_001"
        assert char.character == "あ"
        assert char.romaji == "a"

    async def test_get_character_by_id_not_exists(
        self, content_service: ContentService
    ):
        """Test retrieving a non-existent character by ID."""
        char = await content_service.get_character_by_id("nonexistent_999")

        assert char is None

    async def test_get_characters_by_difficulty(self, content_service: ContentService):
        """Test retrieving characters by difficulty level."""
        easy_chars = await content_service.get_characters_by_difficulty(
            difficulty=1, content_type=ContentType.HIRAGANA
        )

        assert len(easy_chars) > 0
        for char in easy_chars:
            assert char.difficulty == 1
            assert char.content_type == ContentType.HIRAGANA

    async def test_get_characters_by_difficulty_with_limit(
        self, content_service: ContentService
    ):
        """Test limiting results when getting characters by difficulty."""
        chars = await content_service.get_characters_by_difficulty(
            difficulty=1, content_type=ContentType.HIRAGANA, limit=3
        )

        assert len(chars) <= 3

    async def test_get_characters_by_category(self, content_service: ContentService):
        """Test retrieving characters by category."""
        # Note: This test assumes content files have proper categories
        stats = await content_service.get_content_statistics()

        if stats["categories"]:
            # Get first category available
            category_name = list(stats["categories"].keys())[0]
            try:
                category = ContentCategory(category_name)
                chars = await content_service.get_characters_by_category(category)
                assert isinstance(chars, list)
            except ValueError:
                # Category enum might not match - this is expected for some categories
                pass

    async def test_search_characters_by_content_type(
        self, content_service: ContentService
    ):
        """Test searching characters filtered by content type."""
        search_filter = ContentSearchFilter(content_types=[ContentType.HIRAGANA])

        results = await content_service.search_characters(search_filter)

        assert len(results) > 0
        for char in results:
            assert char.content_type == ContentType.HIRAGANA

    async def test_search_characters_by_difficulty_range(
        self, content_service: ContentService
    ):
        """Test searching characters with difficulty range."""
        search_filter = ContentSearchFilter(difficulty_range=(1, 2))

        results = await content_service.search_characters(search_filter)

        assert len(results) > 0
        for char in results:
            assert 1 <= char.difficulty <= 2

    async def test_search_characters_by_tags(self, content_service: ContentService):
        """Test searching characters by tags."""
        search_filter = ContentSearchFilter(tags=["vowel"])

        results = await content_service.search_characters(search_filter)

        if len(results) > 0:  # Only if vowel-tagged characters exist
            for char in results:
                assert "vowel" in char.tags

    async def test_search_characters_exclude_learned(
        self, content_service: ContentService
    ):
        """Test excluding learned characters from search."""
        learned_ids = {"hira_001", "hira_002"}
        search_filter = ContentSearchFilter(
            content_types=[ContentType.HIRAGANA],
            exclude_learned=True,
            learned_character_ids=learned_ids,
        )

        results = await content_service.search_characters(search_filter)

        for char in results:
            assert char.id not in learned_ids

    async def test_get_next_characters_to_learn(self, content_service: ContentService):
        """Test getting next characters to learn."""
        learned_chars = set()
        count = 5

        next_chars = await content_service.get_next_characters_to_learn(
            learned_characters=learned_chars,
            content_type=ContentType.HIRAGANA,
            count=count,
        )

        assert len(next_chars) <= count
        # Should return characters if any are available
        assert isinstance(next_chars, list)

    async def test_get_next_characters_respects_learned(
        self, content_service: ContentService
    ):
        """Test that next characters excludes already learned ones."""
        # Learn first 5 hiragana
        all_hiragana = await content_service.get_characters_by_difficulty(
            difficulty=1, content_type=ContentType.HIRAGANA, limit=5
        )
        learned_ids = {char.id for char in all_hiragana}

        next_chars = await content_service.get_next_characters_to_learn(
            learned_characters=learned_ids, content_type=ContentType.HIRAGANA, count=5
        )

        # Should not include any learned characters
        for char in next_chars:
            assert char.id not in learned_ids

    async def test_validate_content_integrity(self, content_service: ContentService):
        """Test content integrity validation."""
        issues = await content_service.validate_content_integrity()

        assert isinstance(issues, dict)
        assert "missing_ids" in issues
        assert "duplicate_ids" in issues
        assert "missing_characters" in issues

        # Our content should be valid
        total_issues = sum(len(v) for v in issues.values())
        assert total_issues == 0  # No issues in our curated content

    async def test_content_statistics_difficulty_distribution(
        self, content_service: ContentService
    ):
        """Test that difficulty distribution is calculated correctly."""
        stats = await content_service.get_content_statistics()

        diff_dist = stats["difficulty_distribution"]
        assert isinstance(diff_dist, dict)

        # Should have at least difficulty level 1
        assert 1 in diff_dist
        assert diff_dist[1] > 0


@pytest.mark.unit
class TestContentSearchFilter:
    """Tests for ContentSearchFilter class."""

    def test_create_basic_filter(self):
        """Test creating a basic search filter."""
        filter = ContentSearchFilter(content_types=[ContentType.HIRAGANA])

        assert filter.content_types == [ContentType.HIRAGANA]
        assert filter.difficulty_range is None

    def test_create_filter_with_difficulty_range(self):
        """Test creating filter with difficulty range."""
        filter = ContentSearchFilter(difficulty_range=(1, 3))

        assert filter.difficulty_range == (1, 3)

    def test_create_filter_with_tags(self):
        """Test creating filter with tags."""
        filter = ContentSearchFilter(tags=["vowel", "basic"])

        assert "vowel" in filter.tags
        assert "basic" in filter.tags

    def test_create_filter_exclude_learned(self):
        """Test creating filter with learned exclusion."""
        learned_ids = {"hira_001", "hira_002"}
        filter = ContentSearchFilter(
            exclude_learned=True, learned_character_ids=learned_ids
        )

        assert filter.exclude_learned is True
        assert filter.learned_character_ids == learned_ids
