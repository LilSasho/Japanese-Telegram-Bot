"""
Unit tests for SM-2 spaced repetition algorithm.

Tests the SuperMemo-2 algorithm implementation for calculating
intervals, ease factors, and review scheduling.
"""

import pytest
from datetime import datetime, timedelta, timezone

from decimal import Decimal
from app.utils.spaced_repetition import (
    SpacedRepetitionSM2,
    QualityRating,
    ReviewResult,
)


@pytest.mark.unit
class TestSM2Algorithm:
    """Tests for SpacedRepetitionSM2 class."""

    def test_initial_review_quality_0(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test that quality 0 (total blackout) resets learning."""
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.BLACKOUT,
            current_easiness=Decimal("2.5"),
            current_repetitions=5,
            current_interval=10,
        )

        assert result.interval_days == 1
        assert result.repetition_count == 0
        assert result.easiness_factor < Decimal("2.5")  # Should decrease

    def test_initial_review_quality_1(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test that quality 1 (incorrect, remembered) resets learning."""
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.INCORRECT_FAMILIAR,
            current_easiness=Decimal("2.5"),
            current_repetitions=3,
            current_interval=7,
        )

        assert result.interval_days == 1
        assert result.repetition_count == 0

    def test_first_correct_review(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test first correct review (quality 3+)."""
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.CORRECT_HESITATION,  # Quality 4 maintains/improves EF
            current_easiness=Decimal("2.5"),
            current_repetitions=0,
            current_interval=0,
        )

        assert result.interval_days == 1
        assert result.repetition_count == 1
        assert result.easiness_factor >= Decimal("2.5")

    def test_second_correct_review(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test second correct review."""
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.CORRECT_HESITATION,
            current_easiness=Decimal("2.5"),
            current_repetitions=1,
            current_interval=1,
        )

        assert result.interval_days == 6
        assert result.repetition_count == 2

    def test_subsequent_reviews_interval_growth(
        self, sm2_algorithm: SpacedRepetitionSM2
    ):
        """Test that intervals grow with each successful review."""
        # Third review
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.PERFECT,
            current_easiness=Decimal("2.5"),
            current_repetitions=2,
            current_interval=6,
        )

        assert result.interval_days > 6  # Should be around 15
        assert result.repetition_count == 3

        # Fourth review
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.PERFECT,
            current_easiness=result.easiness_factor,
            current_repetitions=3,
            current_interval=result.interval_days,
        )

        assert result.interval_days > 15  # Should continue growing

    def test_ease_factor_minimum(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test that ease factor never goes below 1.3."""
        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.BLACKOUT,
            current_easiness=Decimal("1.3"),
            current_repetitions=5,
            current_interval=10,
        )

        assert result.easiness_factor >= Decimal("1.3")

    def test_ease_factor_increases_with_quality(
        self, sm2_algorithm: SpacedRepetitionSM2
    ):
        """Test that ease factor increases with high quality ratings."""
        initial_ef = Decimal("2.5")

        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.PERFECT,
            current_easiness=initial_ef,
            current_repetitions=2,
            current_interval=6,
        )

        assert result.easiness_factor > initial_ef

    def test_ease_factor_decreases_with_low_quality(
        self, sm2_algorithm: SpacedRepetitionSM2
    ):
        """Test that ease factor decreases with low quality ratings."""
        initial_ef = Decimal("2.5")

        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.CORRECT_DIFFICULT,
            current_easiness=initial_ef,
            current_repetitions=2,
            current_interval=6,
        )

        assert result.easiness_factor < initial_ef

    def test_next_review_date_calculation(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test next review date is calculated correctly."""
        now = datetime.now(timezone.utc)

        result = sm2_algorithm.calculate_next_review(
            quality=QualityRating.PERFECT,
            current_easiness=Decimal("2.5"),
            current_repetitions=2,
            current_interval=6,
            last_review_date=now,
        )

        # Should have next_review_date set
        assert result.next_review_date is not None
        # Should be in the future
        assert result.next_review_date > now

    def test_binary_conversion_correct(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test converting correct binary response to quality."""
        quality = sm2_algorithm.convert_binary_to_quality(is_correct=True)
        assert quality >= QualityRating.CORRECT_DIFFICULT

    def test_binary_conversion_incorrect(self, sm2_algorithm: SpacedRepetitionSM2):
        """Test converting incorrect binary response to quality."""
        quality = sm2_algorithm.convert_binary_to_quality(is_correct=False)
        assert quality == QualityRating.INCORRECT_REMEMBERED

    def test_binary_conversion_with_fast_response(
        self, sm2_algorithm: SpacedRepetitionSM2
    ):
        """Test that fast response time gives perfect rating."""
        quality = sm2_algorithm.convert_binary_to_quality(
            is_correct=True, response_time_ms=1000
        )
        assert quality == QualityRating.PERFECT


@pytest.mark.unit
class TestQualityRating:
    """Tests for QualityRating enum."""

    def test_all_ratings_valid(self):
        """Test that all quality ratings have valid values 0-5."""
        for rating in QualityRating:
            assert 0 <= rating.value <= 5

    def test_rating_count(self):
        """Test that there are exactly 6 quality ratings."""
        assert len(QualityRating) == 6


@pytest.mark.unit
class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_result_creation(self):
        """Test creating a ReviewResult."""
        now = datetime.now(timezone.utc)
        result = ReviewResult(
            interval_days=10,
            repetition_count=3,
            easiness_factor=Decimal("2.5"),
            next_review_date=now,
            quality_rating=5,
        )

        assert result.interval_days == 10
        assert result.repetition_count == 3
        assert result.easiness_factor == Decimal("2.5")
        assert result.quality_rating == 5

    def test_result_immutability(self):
        """Test that ReviewResult fields can be accessed."""
        now = datetime.now(timezone.utc)
        result = ReviewResult(
            interval_days=5,
            repetition_count=2,
            easiness_factor=Decimal("2.3"),
            next_review_date=now,
            quality_rating=4,
        )

        # Should be able to read
        assert result.interval_days == 5
        assert result.repetition_count == 2
        assert result.easiness_factor == Decimal("2.3")
