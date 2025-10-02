"""
Pytest configuration and shared fixtures.

This module provides common fixtures for all test files.
"""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

from app.core.config import Config
from app.core.database import DatabaseManager
from app.services.content_service import ContentService
from app.services.quiz_service import QuizService
from app.services.progress_service import ProgressService
from app.utils.spaced_repetition import SpacedRepetitionSM2


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> Config:
    """Provide a test configuration."""
    config = Config()
    config.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    config.LOG_LEVEL = "ERROR"
    return config


@pytest.fixture
async def db_manager(test_config: Config) -> AsyncGenerator[DatabaseManager, None]:
    """Provide a database manager with in-memory database."""
    manager = DatabaseManager(test_config.DATABASE_URL)
    await manager.init_database()
    yield manager
    # Cleanup handled by in-memory database


@pytest.fixture
async def content_service() -> AsyncGenerator[ContentService, None]:
    """Provide an initialized content service."""
    service = ContentService()
    await service.initialize()
    yield service


@pytest.fixture
async def quiz_service(content_service: ContentService) -> QuizService:
    """Provide a quiz service with content loaded."""
    return QuizService(content_service)


@pytest.fixture
async def progress_service(
    db_manager: DatabaseManager, content_service: ContentService
) -> AsyncGenerator[ProgressService, None]:
    """Provide a progress service with database session."""
    async with db_manager.get_session() as session:
        yield ProgressService(session, content_service)


@pytest.fixture
def sm2_algorithm() -> SpacedRepetitionSM2:
    """Provide an SM-2 algorithm instance."""
    return SpacedRepetitionSM2()


# Sample test data fixtures


@pytest.fixture
def sample_hiragana_chars() -> list[dict]:
    """Provide sample hiragana character data."""
    return [
        {
            "id": "hira_001",
            "character": "あ",
            "romaji": "a",
            "pronunciation": "/a/",
            "meaning": "vowel sound 'ah'",
            "difficulty": 1,
        },
        {
            "id": "hira_002",
            "character": "い",
            "romaji": "i",
            "pronunciation": "/i/",
            "meaning": "vowel sound 'ee'",
            "difficulty": 1,
        },
        {
            "id": "hira_003",
            "character": "う",
            "romaji": "u",
            "pronunciation": "/u/",
            "meaning": "vowel sound 'oo'",
            "difficulty": 1,
        },
    ]


@pytest.fixture
def sample_katakana_chars() -> list[dict]:
    """Provide sample katakana character data."""
    return [
        {
            "id": "kata_001",
            "character": "ア",
            "romaji": "a",
            "pronunciation": "/a/",
            "meaning": "vowel sound 'ah'",
            "difficulty": 1,
        },
        {
            "id": "kata_002",
            "character": "イ",
            "romaji": "i",
            "pronunciation": "/i/",
            "meaning": "vowel sound 'ee'",
            "difficulty": 1,
        },
    ]


@pytest.fixture
def sample_kanji_chars() -> list[dict]:
    """Provide sample kanji character data."""
    return [
        {
            "id": "kanji_001",
            "character": "一",
            "romaji": "ichi",
            "pronunciation": "/itɕi/",
            "meaning": "one",
            "difficulty": 1,
            "stroke_count": 1,
        },
        {
            "id": "kanji_002",
            "character": "二",
            "romaji": "ni",
            "pronunciation": "/ni/",
            "meaning": "two",
            "difficulty": 1,
            "stroke_count": 2,
        },
    ]
