import logging

import pandas as pd

# from scipy.stats import pearsonr

from config import ANALYSIS_CONFIG
from src.plotting import plot_analysis_pearson, plot_gamm
from src.gamm import fit_gamm

logger = logging.getLogger(__name__)


def run_analysis(data):
    """
    Run GAMM analyses for Raven parameters, variability,
    and rhythmic analysis.

    Age or Temperature is the main predictor.
    Insect ID is always the random effect.
    The other variable and Date are optional covariates.
    """

    analysis_config = ANALYSIS_CONFIG["analysis"]
    plotting_config = ANALYSIS_CONFIG["plotting"]

    selections = analysis_config["selections"]
    parameters = analysis_config["parameters"]
    analysis_groups = analysis_config["analysis_groups"]
    variability_parameters = analysis_config["variability"]
    rhythmic_parameters = analysis_config["rhytmic_analysis"]

    results = []

    # ---------------------------------------------------------
    # Helper to run one analysis
    # ---------------------------------------------------------

    def run_one(group, selection, parameter, path):
        result = analyze_parameter_gamm(
            data=data,
            variable=group["predictor"],
            predictor=group["predictor"],
            selection=selection,
            parameter=parameter,
            path=path,
            plot=plotting_config.get("show_plot", False),
            include_age=group["include_age"],
            include_temperature=group["include_temperature"],
            include_date=group["include_date"],
            random_slope=True,
        )

        if result is not None:
            results.append(result)

    # ---------------------------------------------------------
    # 1. Raven parameters: analyze each selection
    # ---------------------------------------------------------

    for group in analysis_groups:
        for selection in selections:
            for parameter in parameters:
                run_one(
                    group=group,
                    selection=selection,
                    parameter=parameter,
                    path=["raven"],
                )

    # ---------------------------------------------------------
    # 2. Variability: no Raven selection required
    # ---------------------------------------------------------

    for group in analysis_groups:
        for parameter in variability_parameters:
            run_one(
                group=group,
                selection=None,
                parameter=parameter,
                path=["variability"],
            )

    # ---------------------------------------------------------
    # 3. Rhythmic analysis: no Raven selection required
    # ---------------------------------------------------------

    for group in analysis_groups:
        for parameter in rhythmic_parameters:
            run_one(
                group=group,
                selection=None,
                parameter=parameter,
                path=["rhytmic_analysis"],
            )

    logger.info(
        "Analysis completed. Successfully fitted %d GAMM models.",
        len(results),
    )

    return results


def get_data_by_path(entry, path):

    value = entry

    for key in path:
        value = value[key]

    return value


def get_numeric_value(values, dataset_id, selection, parameter):
    """
    Return the numeric value from one or more parameter values.

    If multiple values are present, non-numeric values are ignored.
    If multiple numeric values remain, the first one is used and a
    warning is logged.
    """

    numeric_values = pd.to_numeric(
        pd.Series(values),
        errors="coerce",
    ).dropna()

    if numeric_values.empty:
        logger.warning(
            "Dataset %s: no numeric value found for "
            "%s / %s.",
            dataset_id,
            selection,
            parameter,
        )
        return None

    # if len(numeric_values) > 1:
    #     logger.warning(
    #         "Dataset %s: multiple numeric values found for "
    #         "%s / %s: %s. Using first.",
    #         dataset_id,
    #         selection,
    #         parameter,
    #         numeric_values.tolist(),
    #     )

    return numeric_values.iloc[0]

def analyze_parameter_pearson(data, variable, selection, parameter, path):
    # This is a simple Pearsons coefficient

    significance_level = ANALYSIS_CONFIG["statistics"]["significance_level"]

    x = []
    y = []

    for dataset_id, entry in data.items():

        metadata = entry["metadata"]

        # Get predictor variable
        if variable == "age":
            x_value = metadata["Age"]

        elif variable == "date":
            x_value = metadata["Date"]

        else:
            raise ValueError(f"Unknown variable: {variable}")

        # Get data from requested path
        source = get_data_by_path(entry, path)

        # Raven data
        if selection is not None:

            selected = source[
                source["Type"].astype(str).str.strip()
                == selection
            ]

            if parameter not in selected.columns:
                logger.warning(
                    "Dataset %s: parameter '%s' not found "
                    "for selection '%s'",
                    dataset_id,
                    parameter,
                    selection,
                )
                continue

            value = get_numeric_value(
                selected[parameter],
                dataset_id,
                selection,
                parameter,
            )

            if value is None:
                continue

            values = [value]

        # Dataset-level parameters
        else:
            if parameter not in source:
                logger.warning(
                    "Dataset %s: parameter '%s' not found",
                    dataset_id,
                    parameter,
                )
                continue

            values = [source[parameter]]

        # logger.debug(
        #   "Available parameters for %s - %s: %s",
        #   dataset_id,
        #   selection,
        #   list(selected.columns),
        #   )

        for value in values:
            x.append(x_value)
            y.append(value)

    # Convert predictor to numeric
    if variable == "age":
        x = pd.to_numeric(x, errors="coerce")

    elif variable == "date":

        original_dates = pd.Series(x)

        converted_dates = pd.to_datetime(
            original_dates,
            format="%d/%m/%Y",
            errors="coerce",
        )

        days_since_first = (
            converted_dates - converted_dates.min()).dt.days

        # print(
        #   pd.DataFrame({
        #   "Original Date": original_dates,
        #   "Days Since First Recording": days_since_first,
        # }).to_string(index=False)
        # )

        x = days_since_first

    # Convert parameter to numeric
    y = pd.to_numeric(y, errors="coerce")

    # Convert to pandas Series
    x = pd.Series(x)
    y = pd.Series(y)

    # Remove missing values
    valid = x.notna() & y.notna()

    # # Debug: show values that will be deleted
    # deleted = pd.DataFrame({
    #   "x": x[~valid],
    #   "y": y[~valid],
    # })

    # if not deleted.empty:
    #   logger.info("Deleted values:\n%s", deleted)

    x = x[valid]
    y = y[valid]

    # Check that there are enough values
    if len(x) < 3:
        logger.warning(
            "Not enough data for %s - %s - %s (n=%d)",
            variable,
            selection,
            parameter,
            len(x),
        )
        return None

    # ============================================
    # # Debug: show data used for correlation
    # debug_data = pd.DataFrame({
    #   variable: x,
    #   parameter: y,   
    # })

    # print("\n" + "=" * 80)
    # print(f"{variable} vs {parameter} | selection: {selection}")
    # print(f"n = {len(debug_data)}")
    # print("=" * 80)
    # print(debug_data.to_string(index=False))
    # ============================================

    # Calculate Pearson correlation
    r, p = pearsonr(x, y)

    # Report result
    logger.info(
        "%s | %s | %s: r = %.3f, p = %.4f, n = %d",
        variable,
        selection,
        parameter,
        r,
        p,
        len(x),
    )

    if p < significance_level:
        logger.warning(
            "\033[92mCorrelation found: %s - %s - %s\033[0m",
            variable,
            selection,
            parameter,
        )

    else:
        logger.info(
            "No significant correlation: %s - %s - %s",
            variable,
            selection,
            parameter,
        )

    return {
        "variable": variable,
        "selection": selection,
        "parameter": parameter,
        "r": r,
        "p": p,
        "n": len(x),
        "x": x,
        "y": y,
    }

# ==============================
# Gamm model
# ==============================

def analyze_parameter_gamm(
    data,
    variable,
    selection,
    parameter,
    path,
    plot,
    predictor="Age",
    include_age=False,
    include_date=False,
    include_temperature=False,
    random_slope=True,
):
    """
    Fit a GAMM using Age or Temperature as the main predictor.

    Insect ID is always the random effect.
    The other variables can be included as optional covariates.

    If model fitting fails, plot the observed data without
    a fitted curve.
    """

    # ---------------------------------------------------------
    # Validate predictor
    # ---------------------------------------------------------

    if predictor not in ("Age", "Temperature"):
        raise ValueError(
            "predictor must be either 'Age' or 'Temperature'."
        )

    rows = []

    # ---------------------------------------------------------
    # Collect observations
    # ---------------------------------------------------------

    for dataset_id, entry in data.items():
        metadata = entry.get("metadata", {})

        insect_id = metadata.get("ID")

        if insect_id is None or pd.isna(insect_id):
            logger.warning(
                "Skipping dataset %s: missing ID.",
                dataset_id,
            )
            continue

        # The selected predictor must be present and numeric.
        try:
            predictor_value = float(metadata.get(predictor))
        except (TypeError, ValueError):
            logger.warning(
                "Skipping dataset %s: missing or invalid %s.",
                dataset_id,
                predictor,
            )
            continue

        if not pd.notna(predictor_value):
            logger.warning(
                "Skipping dataset %s: invalid %s.",
                dataset_id,
                predictor,
            )
            continue

        response_data = get_data_by_path(entry, path)

        if response_data is None:
            logger.warning(
                "Skipping dataset %s: no data at path %s.",
                dataset_id,
                path,
            )
            continue

        # -----------------------------------------------------
        # Extract response
        # -----------------------------------------------------

        if selection is not None:
            if not isinstance(response_data, pd.DataFrame):
                logger.warning(
                    "Skipping dataset %s: expected Raven DataFrame, got %s.",
                    dataset_id,
                    type(response_data).__name__,
                )
                continue

            if "Type" not in response_data.columns:
                logger.warning(
                    "Skipping dataset %s: Raven data has no Type column.",
                    dataset_id,
                )
                continue

            selection_data = response_data[
                response_data["Type"]
                .astype(str)
                .str.strip()
                .str.lower()
                == str(selection).strip().lower()
            ]

            if selection_data.empty:
                logger.warning(
                    "Skipping dataset %s: selection '%s' not found.",
                    dataset_id,
                    selection,
                )
                continue

            if parameter not in selection_data.columns:
                logger.warning(
                    "Skipping dataset %s: parameter '%s' is not a Raven column.",
                    dataset_id,
                    parameter,
                )
                continue

            # Waveform and Spectrogram may produce duplicate rows.
            values = pd.to_numeric(
                selection_data[parameter],
                errors="coerce",
            ).dropna()

            if values.empty:
                logger.warning(
                    "Skipping dataset %s: no numeric value for '%s'.",
                    dataset_id,
                    parameter,
                )
                continue

            response = float(values.iloc[0])

        else:
            response = response_data

            if isinstance(response, dict):
                response = response.get(parameter)

            try:
                response = float(response)
            except (TypeError, ValueError):
                logger.warning(
                    "Skipping dataset %s: invalid response for '%s'.",
                    dataset_id,
                    parameter,
                )
                continue

        if not pd.notna(response):
            continue

        # -----------------------------------------------------
        # Create observation row
        # -----------------------------------------------------

        row = {
            "Age": metadata.get("Age"),
            "Temperature": metadata.get("Temperature"),
            "Response": response,
            "ID": insect_id,
        }

        # -----------------------------------------------------
        # Optional date
        # -----------------------------------------------------

        if include_date:
            recording_date = pd.to_datetime(
                metadata.get("Date"),
                errors="coerce",
            )

            if pd.notna(recording_date):
                row["Date"] = recording_date
                row["DateDays"] = recording_date.toordinal()
            else:
                row["Date"] = pd.NaT
                row["DateDays"] = None

        rows.append(row)

    # ---------------------------------------------------------
    # Prepare dataframe
    # ---------------------------------------------------------

    if not rows:
        logger.warning(
            "No valid observations for '%s' / '%s'.",
            selection,
            parameter,
        )
        return None

    dataframe = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # Define covariates
    # ---------------------------------------------------------

    covariate_columns = []

    # Do not include the main predictor again as a covariate.
    if include_age and predictor != "Age":
        covariate_columns.append("Age")

    if include_temperature and predictor != "Temperature":
        covariate_columns.append("Temperature")

    if include_date:
        covariate_columns.append("DateDays")

    # The main predictor must always be present.
    required_columns = list(dict.fromkeys([
        predictor,
        "Response",
        "ID",
        *covariate_columns,
    ]))

    numeric_columns = list(dict.fromkeys([
        predictor,
        "Response",
        *covariate_columns,
    ]))

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    dataframe = dataframe.dropna(
        subset=required_columns
    ).copy()

    # ---------------------------------------------------------
    # Check observations
    # ---------------------------------------------------------

    if dataframe.empty:
        logger.warning(
            "No complete observations for '%s' / '%s' "
            "using predictor '%s'.",
            selection,
            parameter,
            predictor,
        )
        return None

    logger.info(
        "Prepared data for selection=%s, parameter=%s, "
        "predictor=%s: n=%d observations, %d insects.",
        selection,
        parameter,
        predictor,
        len(dataframe),
        dataframe["ID"].nunique(),
    )

    # ---------------------------------------------------------
    # Fit GAMM when there is sufficient data
    # ---------------------------------------------------------

    result = None
    fitting_error = None

    if len(dataframe) < 5:
        fitting_error = "fewer than 5 observations"

        logger.warning(
            "Not enough observations to fit GAMM for '%s' / '%s' "
            "using %s (n=%d).",
            selection,
            parameter,
            predictor,
            len(dataframe),
        )

    elif dataframe["ID"].nunique() < 2:
        fitting_error = "fewer than 2 insects"

        logger.warning(
            "GAMM requires at least two insects for '%s' / '%s'.",
            selection,
            parameter,
        )

    else:
        try:
            result = fit_gamm(
                dataframe=dataframe,
                response="Response",
                predictor_column=predictor,
                id_column="ID",
                covariate_columns=covariate_columns,
                spline_df=4,
                random_slope=random_slope,
            )

            if result is None:
                fitting_error = "fit_gamm returned None"

        except Exception as exc:
            fitting_error = str(exc)

            logger.exception(
                "GAMM fitting failed for '%s' / '%s' "
                "using predictor '%s'. The observed-data plot "
                "will still be generated.",
                selection,
                parameter,
                predictor,
            )

    # ---------------------------------------------------------
    # Log successful model
    # ---------------------------------------------------------

    if result is not None:
        logger.info(
            "GAMM fitted: selection=%s, parameter=%s, "
            "predictor=%s, covariates=%s, n=%d, insects=%d",
            selection,
            parameter,
            predictor,
            covariate_columns,
            len(dataframe),
            dataframe["ID"].nunique(),
        )

        try:
            logger.info("%s", result.summary())
        except Exception:
            logger.warning(
                "Could not display model summary for '%s'.",
                parameter,
            )

    # ---------------------------------------------------------
    # Plot even if model fitting failed
    # ---------------------------------------------------------

    if plot:
        try:
            plot_gamm(
                dataframe=dataframe,
                result=result,
                variable=predictor,
                selection=selection,
                parameter=parameter,
                include_age=include_age,
                include_temperature=include_temperature,
                include_date=include_date,
                covariate_columns=covariate_columns,
            )

        except Exception:
            logger.exception(
                "Plotting failed for '%s' / '%s' "
                "using predictor '%s'.",
                selection,
                parameter,
                predictor,
            )

    # ---------------------------------------------------------
    # Report fitting failure
    # ---------------------------------------------------------

    if result is None:
        logger.warning(
            "No fitted model returned for '%s' / '%s'. "
            "Observed-data plot generated if plotting was enabled. "
            "Reason: %s.",
            selection,
            parameter,
            fitting_error or "model fitting failed",
        )

    return result