import logging

import numpy as np
import pandas as pd

from config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)


def add_parameter_variability(data):

    parameters = ANALYSIS_CONFIG["analysis"]["parameters"]
    beeps = ["b1", "b2", "b3", "b4", "b5"]

    for dataset_id, entry in data.items():

        raven = entry["raven"]

        # Create the variability dictionary if it doesn't exist.
        variability = entry.setdefault("variability", {})

        for parameter in parameters:

            values = []

            for beep in beeps:

                selected = raven[
                    raven["Type"].astype(str).str.strip() == beep
                ]

                if selected.empty:
                    logger.warning(
                        "Dataset %s: no %s selection found.",
                        dataset_id,
                        beep,
                    )
                    values = []
                    break

                numeric_values = pd.to_numeric(
                    selected[parameter],
                    errors="coerce",
                ).dropna()

                if numeric_values.empty:
                    logger.warning(
                        "Dataset %s: no numeric value for %s, "
                        "parameter '%s'.",
                        dataset_id,
                        beep,
                        parameter,
                    )
                    values = []
                    break

                # if len(numeric_values) > 1:
                #     logger.warning(
                #         "Dataset %s: multiple numeric values for %s, "
                #         "parameter '%s'. Using the first.",
                #         dataset_id,
                #         beep,
                #         parameter,
                #     )

                values.append(numeric_values.iloc[0])
            
            if len(values) != 5:
                continue

            mean_value = np.mean(values)

            if np.isclose(mean_value, 0):
                logger.warning(
                    "Dataset %s: mean is zero for parameter '%s'.",
                    dataset_id,
                    parameter,
                )
                continue

            # Coefficient of variation = sample SD / mean.
            variability[f"{parameter} Variability"] = (
                np.std(values, ddof=1) / mean_value
            )

    return data
