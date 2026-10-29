import logging

import pandas as pd
import statsmodels.formula.api as smf
import numpy as np
from patsy import bs


logger = logging.getLogger(__name__)

def fit_gamm(
    dataframe,
    response,
    predictor_column,
    id_column,
    covariate_columns=None,
    spline_df=4,
    random_slope=True,
):
    """
    Fit a spline-based mixed-effects model.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Analysis data.
    response : str
        Response variable column.
    predictor_column : str
        Main predictor, e.g. "Age" or "Temperature".
    id_column : str
        Grouping variable for insect random effects.
    covariate_columns : list or None
        Optional fixed-effect covariates, e.g. ["DateDays"].
    spline_df : int
        Degrees of freedom for the predictor spline.
    random_slope : bool
        Include a random linear slope for the main predictor.

    Returns
    -------
    Fitted statsmodels MixedLM result, or None if fitting fails.
    """

    if covariate_columns is None:
        covariate_columns = []

    # ---------------------------------------------------------
    # Validate data
    # ---------------------------------------------------------

    required_columns = [
        response,
        predictor_column,
        id_column,
        *covariate_columns,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    model_data = dataframe[required_columns].copy()

    # Convert model variables to numeric.
    numeric_columns = [
        response,
        predictor_column,
        *covariate_columns,
    ]

    for column in numeric_columns:
        model_data[column] = pd.to_numeric(
            model_data[column],
            errors="coerce",
        )

    model_data = model_data.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    model_data[id_column] = model_data[id_column].astype(str)

    if len(model_data) < 5:
        logger.warning("Insufficient observations for mixed model.")
        return None

    if model_data[id_column].nunique() < 2:
        logger.warning("At least two insects are required.")
        return None

    if model_data[predictor_column].nunique() < 2:
        logger.warning(
            "Predictor '%s' has no variation.",
            predictor_column,
        )
        return None

    # ---------------------------------------------------------
    # Build fixed-effects formula
    # ---------------------------------------------------------

    fixed_terms = [
        f"bs(Q('{predictor_column}'), df={spline_df}, degree=3)"
    ]

    for column in covariate_columns:
        fixed_terms.append(f"Q('{column}')")

    formula = f"Q('{response}') ~ " + " + ".join(fixed_terms)

    # ---------------------------------------------------------
    # Build random-effects structure
    # ---------------------------------------------------------

    if random_slope:
        random_formula = f"1 + Q('{predictor_column}')"
    else:
        random_formula = "1"

    # ---------------------------------------------------------
    # Fit model
    # ---------------------------------------------------------

    try:
        model = smf.mixedlm(
            formula=formula,
            data=model_data,
            groups=model_data[id_column],
            re_formula=random_formula,
        )

        result = model.fit(
            reml=False,
            method="lbfgs",
            maxiter=1000,
            disp=False,
        )

        if not result.converged:
            logger.warning(
                "Mixed model did not converge using random_slope=%s.",
                random_slope,
            )

            # Retry with a random intercept only if the random-slope
            # model failed to converge.
            if random_slope:
                logger.info(
                    "Retrying model with a random intercept only."
                )

                model = smf.mixedlm(
                    formula=formula,
                    data=model_data,
                    groups=model_data[id_column],
                    re_formula="1",
                )

                result = model.fit(
                    reml=False,
                    method="lbfgs",
                    maxiter=1000,
                    disp=False,
                )

                if not result.converged:
                    logger.warning(
                        "Random-intercept model also failed to converge."
                    )
                    return None

        return result

    except Exception:
        logger.exception("Failed to fit mixed-effects model.")
        return None