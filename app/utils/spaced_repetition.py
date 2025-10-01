"""
Spaced Repetition Algorithm (SM-2) for the Japanese Learning Telegram Bot.

This module implements the SuperMemo 2 (SM-2) algorithm for optimizing
learning intervals based on user performance. The algorithm adjusts review
schedules dynamically to maximize long-term retention.

References:
    - Original SM-2 Algorithm: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
    - Modified for language learning with Japanese character acquisition
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import IntEnum
from typing import Optional


class QualityRating(IntEnum):
    """Quality ratings for SM-2 algorithm.

    These ratings represent how well the user recalled the information:
    - 0: Complete blackout (no recall)
    - 1: Incorrect with correct answer feeling familiar
    - 2: Incorrect but remembered upon seeing answer
    - 3: Correct with difficulty
    - 4: Correct with hesitation
    - 5: Perfect recall
    """

    BLACKOUT = 0
    INCORRECT_FAMILIAR = 1
    INCORRECT_REMEMBERED = 2
    CORRECT_DIFFICULT = 3
    CORRECT_HESITATION = 4
    PERFECT = 5


@dataclass
class ReviewResult:
    """Result of a spaced repetition calculation.

    Attributes:
        easiness_factor: Updated easiness factor (1.3 - 2.5+)
        repetition_count: Number of successful consecutive repetitions
        interval_days: Days until next review
        next_review_date: Calculated next review date
        quality_rating: The quality rating that produced this result
    """

    easiness_factor: Decimal
    repetition_count: int
    interval_days: int
    next_review_date: datetime
    quality_rating: int


class SpacedRepetitionSM2:
    """Implementation of the SuperMemo 2 (SM-2) spaced repetition algorithm.

    This class provides methods to calculate optimal review intervals based on
    user performance, helping to maximize long-term retention of learned material.

    The algorithm maintains three key parameters:
    - Easiness Factor (EF): Reflects item difficulty (1.3 minimum, 2.5 default)
    - Repetition Count (n): Number of consecutive successful reviews
    - Interval (I): Days until next review

    Example:
        >>> sm2 = SpacedRepetitionSM2()
        >>> result = sm2.calculate_next_review(
        ...     quality=QualityRating.CORRECT_HESITATION,
        ...     current_easiness=Decimal("2.5"),
        ...     current_repetitions=0,
        ...     current_interval=1
        ... )
        >>> print(f"Next review in {result.interval_days} days")
    """

    # Algorithm constants
    MIN_EASINESS_FACTOR = Decimal("1.3")
    DEFAULT_EASINESS_FACTOR = Decimal("2.5")
    MAX_EASINESS_FACTOR = Decimal("2.5")  # SM-2 doesn't cap, but we do for stability

    # Initial intervals (in days)
    FIRST_INTERVAL = 1
    SECOND_INTERVAL = 6

    # Quality threshold for successful recall
    PASSING_QUALITY = 3  # Ratings >= 3 are considered successful

    def __init__(
        self,
        min_easiness: Optional[Decimal] = None,
        default_easiness: Optional[Decimal] = None,
    ):
        """Initialize the SM-2 calculator.

        Args:
            min_easiness: Minimum easiness factor (default: 1.3)
            default_easiness: Default starting easiness (default: 2.5)
        """
        self.min_easiness = min_easiness or self.MIN_EASINESS_FACTOR
        self.default_easiness = default_easiness or self.DEFAULT_EASINESS_FACTOR

    def calculate_next_review(
        self,
        quality: int,
        current_easiness: Decimal,
        current_repetitions: int,
        current_interval: int,
        last_review_date: Optional[datetime] = None,
    ) -> ReviewResult:
        """Calculate the next review parameters based on user performance.

        This is the core SM-2 algorithm implementation. It updates the easiness
        factor based on recall quality, adjusts the repetition count, and
        calculates the optimal interval until the next review.

        Args:
            quality: Quality rating (0-5) from QualityRating enum
            current_easiness: Current easiness factor for this item
            current_repetitions: Number of consecutive successful reviews
            current_interval: Current interval in days
            last_review_date: Date of last review (defaults to now)

        Returns:
            ReviewResult with updated parameters and next review date

        Raises:
            ValueError: If quality rating is not between 0 and 5
        """
        # Validate quality rating
        if not 0 <= quality <= 5:
            raise ValueError(f"Quality rating must be between 0 and 5, got {quality}")

        # Use current time if last review not provided
        if last_review_date is None:
            last_review_date = datetime.now(timezone.utc)

        # Step 1: Calculate new easiness factor
        new_easiness = self._calculate_easiness_factor(quality, current_easiness)

        # Step 2: Determine if recall was successful
        is_successful = quality >= self.PASSING_QUALITY

        # Step 3: Update repetition count and interval
        if is_successful:
            new_repetitions = current_repetitions + 1
            new_interval = self._calculate_interval(
                new_repetitions, current_interval, new_easiness
            )
        else:
            # Failed recall: reset to beginning
            new_repetitions = 0
            new_interval = self.FIRST_INTERVAL

        # Step 4: Calculate next review date
        next_review_date = self._calculate_next_review_date(
            last_review_date, new_interval
        )

        return ReviewResult(
            easiness_factor=new_easiness,
            repetition_count=new_repetitions,
            interval_days=new_interval,
            next_review_date=next_review_date,
            quality_rating=quality,
        )

    def _calculate_easiness_factor(
        self, quality: int, current_easiness: Decimal
    ) -> Decimal:
        """Calculate new easiness factor based on recall quality.

        The SM-2 formula for easiness factor adjustment:
        EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

        Where:
        - EF' is the new easiness factor
        - EF is the current easiness factor
        - q is the quality rating (0-5)

        Args:
            quality: Quality rating (0-5)
            current_easiness: Current easiness factor

        Returns:
            New easiness factor (minimum 1.3)
        """
        # SM-2 formula for easiness adjustment
        quality_decimal = Decimal(str(quality))
        adjustment = Decimal("0.1") - (Decimal("5") - quality_decimal) * (
            Decimal("0.08") + (Decimal("5") - quality_decimal) * Decimal("0.02")
        )

        new_easiness = current_easiness + adjustment

        # Enforce minimum easiness factor
        new_easiness = max(new_easiness, self.min_easiness)

        return new_easiness

    def _calculate_interval(
        self, repetitions: int, previous_interval: int, easiness: Decimal
    ) -> int:
        """Calculate the interval until next review.

        SM-2 interval calculation:
        - I(1) = 1 day
        - I(2) = 6 days
        - I(n) = I(n-1) * EF (for n > 2)

        Args:
            repetitions: Number of consecutive successful reviews
            previous_interval: Previous interval in days
            easiness: Current easiness factor

        Returns:
            Interval in days (minimum 1)
        """
        if repetitions == 1:
            return self.FIRST_INTERVAL
        elif repetitions == 2:
            return self.SECOND_INTERVAL
        else:
            # For subsequent repetitions, multiply previous interval by easiness
            new_interval = int(previous_interval * float(easiness))
            return max(1, new_interval)  # Ensure at least 1 day

    def _calculate_next_review_date(
        self, last_review: datetime, interval_days: int
    ) -> datetime:
        """Calculate the next review date.

        Args:
            last_review: Date and time of last review
            interval_days: Number of days until next review

        Returns:
            Next review date (set to start of day in UTC)
        """
        # Calculate next review date
        next_review = last_review + timedelta(days=interval_days)

        # Normalize to start of day (00:00:00 UTC)
        next_review = next_review.replace(hour=0, minute=0, second=0, microsecond=0)

        return next_review

    def convert_binary_to_quality(
        self, is_correct: bool, response_time_ms: Optional[int] = None
    ) -> QualityRating:
        """Convert binary correct/incorrect to quality rating.

        This is a helper method for systems that only track correct/incorrect
        without detailed quality ratings. It uses response time to estimate
        the quality of recall.

        Args:
            is_correct: Whether the answer was correct
            response_time_ms: Response time in milliseconds (optional)

        Returns:
            Estimated QualityRating
        """
        if not is_correct:
            return QualityRating.INCORRECT_REMEMBERED

        # If correct but no response time, assume good recall
        if response_time_ms is None:
            return QualityRating.CORRECT_HESITATION

        # Use response time to estimate quality of recall
        if response_time_ms < 2000:
            return QualityRating.PERFECT
        elif 2000 <= response_time_ms < 4000:
            return QualityRating.CORRECT_HESITATION
        else:  # response_time_ms >= 4000
            return QualityRating.CORRECT_DIFFICULT


# Convenience function for quick calculations
def calculate_review(
    quality: int,
    easiness: Decimal = Decimal("2.5"),
    repetitions: int = 0,
    interval: int = 1,
    last_review: Optional[datetime] = None,
) -> ReviewResult:
    """Convenience function to calculate next review without instantiating class.

    Args:
        quality: Quality rating (0-5)
        easiness: Current easiness factor (default: 2.5)
        repetitions: Current repetition count (default: 0)
        interval: Current interval in days (default: 1)
        last_review: Date of last review (default: now)

    Returns:
        ReviewResult with updated parameters
    """
    sm2 = SpacedRepetitionSM2()
    return sm2.calculate_next_review(
        quality=quality,
        current_easiness=easiness,
        current_repetitions=repetitions,
        current_interval=interval,
        last_review_date=last_review,
    )
