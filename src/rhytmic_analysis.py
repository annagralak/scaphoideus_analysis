import logging
import numpy as np
import pandas as pd

from src.plotting import plot_intervals_by_insect
from config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)


def add_rhythmic_analysis(data):
    """
    Calculate rhythmic statistics using all available beep selections.

    Intervals are ordered from the end of the signal:
        Interval 1 = b1 - b2
        Interval 2 = b2 - b3
        etc.

    Mean Interval and Rhythmic Coefficient use filtered intervals:
        - Remove the first five and last five intervals.
        - If more than 15 remain, keep only the first 15.

    Number of Beeps and Minimum Interval use the original intervals.
    """

    show_plot = ANALYSIS_CONFIG["plotting"]["show_plot"]

    for dataset_id, entry in data.items():

        raven = entry["raven"]
        entry["rhytmic_analysis"] = {}

        logger.debug("=" * 70)
        logger.debug("Rhythmic analysis: %s", dataset_id)

        if "Type" not in raven.columns or "Begin Time (s)" not in raven.columns:
            logger.warning(
                "Dataset %s: missing Type or Begin Time (s) column.",
                dataset_id,
            )
            continue

        beep_rows = raven[
            raven["Type"]
            .astype(str)
            .str.strip()
            .str.fullmatch(r"b\d+")
        ]

        beep_times = {}

        for beep, selected in beep_rows.groupby(
            beep_rows["Type"].astype(str).str.strip()
        ):
            times = pd.to_numeric(
                selected["Begin Time (s)"],
                errors="coerce",
            ).dropna()

            if times.empty:
                logger.warning(
                    "Dataset %s: no valid start time for %s.",
                    dataset_id,
                    beep,
                )
                continue

            beep_times[beep] = times.iloc[0]

        if len(beep_times) < 2:
            logger.warning(
                "Dataset %s: fewer than two valid beeps.",
                dataset_id,
            )
            continue

        # Calculate original intervals from b1 backward: b1-b2, b2-b3, etc.
        beep_numbers = sorted(
            int(beep[1:]) for beep in beep_times
        )

        intervals = []

        for number in beep_numbers:
            current_beep = f"b{number}"
            next_beep = f"b{number + 1}"

            if current_beep in beep_times and next_beep in beep_times:
                interval = (
                    beep_times[current_beep] - beep_times[next_beep]
                )
                intervals.append(interval)

        if not intervals or np.any(np.asarray(intervals) <= 0):
            logger.warning(
                "Dataset %s: invalid or non-positive intervals.",
                dataset_id,
            )
            continue

        # Remove the first six and last six intervals.
        filtered_intervals = intervals[5:-5]

        # Keep at most 15 intervals for rhythmic statistics.
        if len(filtered_intervals) > 15:
            filtered_intervals = filtered_intervals[:15]

        # Minimum interval is calculated from the original list.
        minimum_interval = min(intervals)

        # Mean and rhythmic coefficient use the filtered list.
        if filtered_intervals:
            filtered_statistics = calculate_intervals(filtered_intervals)
            mean_interval = filtered_statistics["Mean Interval"]
            rhythmic_coefficient = filtered_statistics["Rhythmic Coefficient"]
        else:
            logger.warning(
                "Dataset %s: no intervals remain after filtering.",
                dataset_id,
            )
            mean_interval = np.nan
            rhythmic_coefficient = np.nan

        entry["rhytmic_analysis"] = {
            "Number of Beeps": len(beep_times),
            "Interval List": intervals,
            "Filtered Interval List": filtered_intervals,
            "Mean Interval": mean_interval,
            "Minimum Interval": minimum_interval,
            "Rhythmic Coefficient": rhythmic_coefficient,
        }

        logger.debug(
            "Dataset %s: %d beeps; original intervals=%s; "
            "filtered intervals=%s",
            dataset_id,
            len(beep_times),
            intervals,
            filtered_intervals,
        )

    if show_plot:
        plot_intervals_by_insect(data)

    return data


def calculate_intervals(values):
    """Calculate mean and coefficient of variation of intervals."""

    values = np.asarray(values, dtype=float)

    mean_interval = np.mean(values)

    if np.isclose(mean_interval, 0) or len(values) < 2:
        rhythmic_coefficient = np.nan
    else:
        rhythmic_coefficient = np.std(values, ddof=1) / mean_interval

    return {
        "Mean Interval": mean_interval,
        "Rhythmic Coefficient": rhythmic_coefficient,
    }