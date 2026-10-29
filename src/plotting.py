import logging

import matplotlib.pyplot as plt
import mplcursors
import numpy as np
import pandas as pd

from config import ANALYSIS_CONFIG

from scipy.stats import linregress

logger = logging.getLogger(__name__)

def plot_analysis_pearson(result):
    """
    Plot the result of one correlation analysis.
    """

    if result is None:
        return

    variable = result["variable"]
    selection = result["selection"]
    parameter = result["parameter"]

    r = result["r"]
    p = result["p"]
    n = result["n"]

    x = result["x"]
    y = result["y"]

    # Get plotting settings
    plotting_config = ANALYSIS_CONFIG["plotting"]

    show_only_significant = plotting_config["show_only_significant"]
    show_values = plotting_config["show_values"]
    show_regression_line = plotting_config["show_regression_line"]
    show_confidence_interval = plotting_config["show_confidence_interval"]

    significance_level = ANALYSIS_CONFIG["statistics"]["significance_level"]

    # Skip non-significant results if configured
    if show_only_significant and p >= significance_level:
        return

    # Convert to numpy arrays
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # -------------------------------------------------
    # Create figure
    # -------------------------------------------------

    fig, ax = plt.subplots(figsize=(8, 6))

    # -------------------------------------------------
    # Scatter plot
    # -------------------------------------------------

    ax.scatter(
        x,
        y,
        s=50,
        alpha=0.75,
        edgecolor="black",
        linewidth=0.5,
    )

    # -------------------------------------------------
    # Regression line
    # -------------------------------------------------

    if show_regression_line and len(x) >= 3:

        regression = linregress(x, y)

        slope = regression.slope
        intercept = regression.intercept

        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = intercept + slope * x_line

        ax.plot(
            x_line,
            y_line,
            linewidth=2,
        )

        # -------------------------------------------------
        # 95% confidence interval
        # -------------------------------------------------

        if show_confidence_interval:

            y_pred = intercept + slope * x

            residuals = y - y_pred
            residual_std = np.sqrt(
                np.sum(residuals ** 2) / (len(x) - 2)
            )

            x_mean = np.mean(x)

            se_mean = residual_std * np.sqrt(
                1 / len(x)
                + (x_line - x_mean) ** 2
                / np.sum((x - x_mean) ** 2)
            )

            # Approximate 95% CI
            ci = 1.96 * se_mean

            ax.fill_between(
                x_line,
                y_line - ci,
                y_line + ci,
                alpha=0.2,
            )

    # -------------------------------------------------
    # Optional value labels
    # -------------------------------------------------

    if show_values:

        for x_value, y_value in zip(x, y):

            ax.annotate(
                f"{y_value:.2f}",
                (x_value, y_value),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )

    # -------------------------------------------------
    # Labels
    # -------------------------------------------------

    if variable == "age":
        x_label = "Age"
    elif variable == "date":
        x_label = "Recording date"
    else:
        x_label = variable

    ax.set_xlabel(x_label)
    ax.set_ylabel(parameter)

    # -------------------------------------------------
    # Title
    # -------------------------------------------------

    significance = ""

    if p < significance_level:
        significance = "significant"
    else:
        significance = "not significant"

    ax.set_title(
        f"{parameter} vs {x_label}\n"
        f"Selection: {selection} | "
        f"r = {r:.3f}, p = {p:.4f}, n = {n} ({significance})"
    )

    # -------------------------------------------------
    # Grid
    # -------------------------------------------------

    ax.grid(
        True,
        alpha=0.3,
    )

    # -------------------------------------------------
    # Layout
    # -------------------------------------------------

    fig.tight_layout()

    plt.show()



def plot_gamm(
    dataframe,
    result,
    variable,
    selection,
    parameter,
    include_date=False,
    covariate_columns=None,
    include_age=False,
    include_temperature=False,
):
    """
    Plot observations and the fitted GAMM relationship.

    Point-color priority:
    1. Age, if included as a covariate.
    2. Temperature, if included as a covariate.
    3. Date, if included as a covariate.
    4. A single color if no eligible covariate is available.

    Observations from the same insect are connected by lines.

    Hover information includes insect ID, recording date,
    Age, Temperature, predictor, and response.

    If model fitting fails, observed data are still plotted.
    """

    if covariate_columns is None:
        covariate_columns = []

    dataframe = dataframe.copy()

    # ---------------------------------------------------------
    # Validate data
    # ---------------------------------------------------------

    required_columns = [variable, "Response"]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        logger.warning(
            "Cannot plot GAMM: missing columns %s.",
            missing_columns,
        )
        return

    dataframe[variable] = pd.to_numeric(
        dataframe[variable],
        errors="coerce",
    )

    dataframe["Response"] = pd.to_numeric(
        dataframe["Response"],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=[variable, "Response"]
    ).copy()

    if dataframe.empty:
        logger.warning(
            "Cannot plot GAMM: no valid observations."
        )
        return

    # Normalize dates for hover information and date coloring.
    if "Date" in dataframe.columns:
        dataframe["Date"] = pd.to_datetime(
            dataframe["Date"],
            errors="coerce",
        )

    # ---------------------------------------------------------
    # Identify the point-color variable
    # ---------------------------------------------------------

    color_by = None

    # Follow the requested priority.
    color_candidates = []

    if include_age and variable != "Age":
        color_candidates.append("Age")

    if include_temperature and variable != "Temperature":
        color_candidates.append("Temperature")

    if include_date:
        color_candidates.append("Date")

    for candidate in color_candidates:
        if candidate not in dataframe.columns:
            continue

        if dataframe[candidate].notna().any():
            color_by = candidate
            break

    # ---------------------------------------------------------
    # Generate predictions
    # ---------------------------------------------------------

    predictions = None
    predictor_grid = None

    if result is not None:
        predictor_values = dataframe[variable].dropna()

        if not predictor_values.empty:
            predictor_grid = np.linspace(
                predictor_values.min(),
                predictor_values.max(),
                100,
            )

            prediction_data = pd.DataFrame({
                variable: predictor_grid,
            })

            prediction_valid = True

            for column in covariate_columns:
                if column not in dataframe.columns:
                    logger.warning(
                        "Cannot predict GAMM: covariate '%s' "
                        "is missing.",
                        column,
                    )
                    prediction_valid = False
                    break

                if pd.api.types.is_numeric_dtype(
                    dataframe[column]
                ):
                    covariate_mean = dataframe[column].mean()

                    if pd.isna(covariate_mean):
                        logger.warning(
                            "Cannot predict GAMM: covariate '%s' "
                            "has no valid numeric values.",
                            column,
                        )
                        prediction_valid = False
                        break

                    prediction_data[column] = covariate_mean

                else:
                    modes = dataframe[column].mode(dropna=True)

                    if modes.empty:
                        logger.warning(
                            "Cannot predict GAMM: no valid value "
                            "for covariate '%s'.",
                            column,
                        )
                        prediction_valid = False
                        break

                    prediction_data[column] = modes.iloc[0]

            if prediction_valid:
                try:
                    predictions = result.predict(prediction_data)

                except Exception:
                    logger.exception(
                        "Could not generate GAMM predictions "
                        "for %s.",
                        parameter,
                    )
                    predictions = None
                    predictor_grid = None
            else:
                predictor_grid = None

    # ---------------------------------------------------------
    # Create plot
    # ---------------------------------------------------------

    fig, ax = plt.subplots(figsize=(11, 7))

    # ---------------------------------------------------------
    # Connect observations from the same insect
    # ---------------------------------------------------------

    if "ID" in dataframe.columns:
        for _, insect_data in dataframe.groupby(
            "ID",
            sort=False,
            dropna=False,
        ):
            insect_data = insect_data.sort_values(variable)

            ax.plot(
                insect_data[variable],
                insect_data["Response"],
                color="gray",
                linewidth=0.8,
                alpha=0.4,
                zorder=1,
            )

    # ---------------------------------------------------------
    # Plot observations
    # ---------------------------------------------------------

    scatter_objects = []

    def add_scatter(
        plot_data,
        color=None,
        label=None,
        values=None,
        cmap="turbo",
    ):
        """Add a scatter layer and retain its source rows for hover."""

        if plot_data.empty:
            return None

        if values is not None:
            scatter = ax.scatter(
                plot_data[variable],
                plot_data["Response"],
                c=values,
                cmap=cmap,
                alpha=0.9,
                edgecolor="black",
                linewidth=0.4,
                s=55,
                zorder=2,
            )
        else:
            scatter = ax.scatter(
                plot_data[variable],
                plot_data["Response"],
                color=color,
                alpha=0.9,
                edgecolor="black",
                linewidth=0.4,
                s=55,
                zorder=2,
                label=label,
            )

        scatter_objects.append((scatter, plot_data.copy()))
        return scatter

    # ---------------------------------------------------------
    # Continuous color scale: Age or Temperature
    # ---------------------------------------------------------

    if color_by in ("Age", "Temperature"):
        dataframe[color_by] = pd.to_numeric(
            dataframe[color_by],
            errors="coerce",
        )

        valid_data = dataframe.dropna(
            subset=[color_by]
        ).copy()

        missing_data = dataframe[
            dataframe[color_by].isna()
        ].copy()

        if not valid_data.empty:
            scatter = add_scatter(
                valid_data,
                values=valid_data[color_by],
            )

            colorbar = fig.colorbar(
                scatter,
                ax=ax,
                pad=0.03,
            )
            
            colorbar.set_label(
                color_by,
                rotation=270,
                labelpad=20,
            )

        # Keep observations without a color value visible.
        if not missing_data.empty:
            add_scatter(
                missing_data,
                color="gray",
                label=f"{color_by} unavailable",
            )

    # ---------------------------------------------------------
    # Categorical color scale: Date
    # ---------------------------------------------------------

    elif color_by == "Date":
        dataframe["Date"] = pd.to_datetime(
            dataframe["Date"],
            errors="coerce",
        )

        unique_dates = sorted(
            dataframe["Date"].dropna().unique()
        )

        cmap = plt.cm.turbo

        positions = np.linspace(
            0.05,
            0.95,
            max(len(unique_dates), 1),
        )

        date_colors = {
            date: cmap(position)
            for date, position in zip(
                unique_dates,
                positions,
            )
        }

        for date in unique_dates:
            date_data = dataframe[
                dataframe["Date"] == date
            ]

            add_scatter(
                date_data,
                color=date_colors[date],
                label=pd.Timestamp(date).strftime("%d/%m/%Y"),
            )

        missing_date = dataframe[
            dataframe["Date"].isna()
        ]

        if not missing_date.empty:
            add_scatter(
                missing_date,
                color="gray",
                label="Date unavailable",
            )

    # ---------------------------------------------------------
    # No covariate available for coloring
    # ---------------------------------------------------------

    else:
        add_scatter(
            dataframe,
            color="tab:blue",
            label="Observed data",
        )

    # ---------------------------------------------------------
    # Hover information
    # ---------------------------------------------------------

    if scatter_objects:
        cursor = mplcursors.cursor(
            [scatter for scatter, _ in scatter_objects],
            hover=mplcursors.HoverMode.Transient,
        )

        @cursor.connect("add")
        def on_add(hover_selection):
            current_scatter = hover_selection.artist

            for scatter, scatter_data in scatter_objects:
                if current_scatter is not scatter:
                    continue

                point_index = int(hover_selection.index)

                if point_index >= len(scatter_data):
                    return

                row = scatter_data.iloc[point_index]
                hover_text = []

                if "ID" in row.index and pd.notna(row["ID"]):
                    hover_text.append(
                        f"Insect ID: {row['ID']}"
                    )

                if (
                    variable in row.index
                    and pd.notna(row[variable])
                ):
                    hover_text.append(
                        f"Predictor ({variable}): "
                        f"{row[variable]:.4f}"
                    )

                if (
                    "Response" in row.index
                    and pd.notna(row["Response"])
                ):
                    hover_text.append(
                        f"{parameter}: {row['Response']:.4f}"
                    )

                if (
                    "Date" in row.index
                    and pd.notna(row["Date"])
                ):
                    hover_text.append(
                        "Recording date: "
                        f"{pd.Timestamp(row['Date']).strftime('%d/%m/%Y')}"
                    )
                else:
                    hover_text.append("Recording date: unavailable")

                for column in ("Age", "Temperature"):
                    if (
                        column in row.index
                        and pd.notna(row[column])
                    ):
                        try:
                            value_text = f"{float(row[column]):.2f}"
                        except (TypeError, ValueError):
                            value_text = str(row[column])

                        hover_text.append(
                            f"{column}: {value_text}"
                        )
                    else:
                        hover_text.append(
                            f"{column}: unavailable"
                        )

                hover_selection.annotation.set_text(
                    "\n".join(hover_text)
                )
                break

    # ---------------------------------------------------------
    # Plot fitted relationship, if available
    # ---------------------------------------------------------

    if predictions is not None and predictor_grid is not None:
        ax.plot(
            predictor_grid,
            predictions,
            color="black",
            linewidth=2.2,
            zorder=3,
            label="Fitted relationship",
        )

    # ---------------------------------------------------------
    # Labels and model configuration
    # ---------------------------------------------------------

    ax.set_xlabel(variable)
    ax.set_ylabel(parameter)

    selection_label = (
        str(selection)
        if selection is not None
        else "None (all data)"
    )

    settings_text = (
        f"Predictor: {variable}\n"
        f"Selection: {selection_label}\n"
        f"Parameter: {parameter}\n"
        f"Include Age: {include_age}\n"
        f"Include Temperature: {include_temperature}\n"
        f"Include Date: {include_date}\n"
        f"Model covariates: "
        f"{', '.join(covariate_columns) if covariate_columns else 'None'}"
    )

    title = (
        f"{selection_label} | {parameter} vs {variable}"
    )

    if result is None:
        title += "\nObserved data only (GAMM fit unavailable)"

    ax.set_title(title)

    # Show model settings directly on the figure.
    ax.text(
        0.02,
        0.98,
        settings_text,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
        fontsize=8,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "alpha": 0.85,
            "edgecolor": "lightgray",
        },
        zorder=4,
    )

    # ---------------------------------------------------------
    # Legend and layout
    # ---------------------------------------------------------

    handles, labels = ax.get_legend_handles_labels()

    if handles:
        ax.legend(
            handles,
            labels,
            title="",
            bbox_to_anchor=(1.15, 1),
            loc="upper left",
            fontsize=8,
            labelspacing=1.0,
            borderaxespad=0,
        )

    ax.grid(True, alpha=0.3)

    if color_by in ("Age", "Temperature"):
        fig.subplots_adjust(
            left=0.10,
            right=0.78,
            bottom=0.12,
            top=0.86,
        )
    elif color_by == "Date":
        fig.subplots_adjust(
            left=0.10,
            right=0.76,
            bottom=0.12,
            top=0.86,
        )
    else:
        fig.tight_layout()

    plt.show()


def plot_intervals_by_insect(data):
    """Plot filtered intervals as solid lines and excluded intervals as dashed lines."""

    fig, ax = plt.subplots(figsize=(14, 8), constrained_layout=True)
    
    # Assign one color per insect.
    insect_ids = list(dict.fromkeys(
        str(entry["metadata"].get("ID", dataset_id))
        for dataset_id, entry in data.items()
    ))

    cmap = plt.cm.turbo
    positions = np.linspace(0.05, 0.95, max(len(insect_ids), 1))
    insect_colors = {
        insect_id: cmap(position)
        for insect_id, position in zip(insect_ids, positions)
    }

    legend_ids = set()
    scatter_objects = []
    max_intervals = 0

    for dataset_id, entry in data.items():
        metadata = entry["metadata"]
        rhythmic = entry.get("rhytmic_analysis", {})

        intervals = rhythmic.get("Interval List", [])
        filtered_intervals = rhythmic.get("Filtered Interval List", [])

        if not intervals:
            continue

        insect_id = str(metadata.get("ID", dataset_id))
        color = insect_colors[insect_id]

        recording_date = pd.to_datetime(
            metadata.get("Date"), errors="coerce"
        )
        date_label = (
            recording_date.strftime("%d/%m/%Y")
            if pd.notna(recording_date)
            else "Unknown"
        )

        interval_numbers = np.arange(1, len(intervals) + 1)
        max_intervals = max(max_intervals, len(intervals))

        # Add the insect to the legend only once.
        insect_label = (
            insect_id if insect_id not in legend_ids else "_nolegend_"
        )
        legend_ids.add(insect_id)

        # The filtered intervals correspond to intervals[5:-5].
        if filtered_intervals:
            filtered_start = 5
            filtered_end = filtered_start + len(filtered_intervals)

            # Dashed: intervals before the filtered range.
            ax.plot(
                interval_numbers[:filtered_start + 1],
                intervals[:filtered_start + 1],
                color=color,
                linewidth=1.2,
                linestyle="--",
                alpha=0.7,
                label=insect_label,
            )

            # Dashed: intervals after the filtered range.
            ax.plot(
                interval_numbers[filtered_end - 1:],
                intervals[filtered_end - 1:],
                color=color,
                linewidth=1.2,
                linestyle="--",
                alpha=0.7,
                label="_nolegend_",
            )

            # Solid: filtered intervals.
            filtered_numbers = np.arange(
                filtered_start + 1,
                filtered_end + 1,
            )
            ax.plot(
                filtered_numbers,
                filtered_intervals,
                color=color,
                linewidth=2,
                linestyle="-",
                alpha=0.9,
                label="_nolegend_",
            )

        else:
            # No filtered intervals: plot all intervals dashed.
            ax.plot(
                interval_numbers,
                intervals,
                color=color,
                linewidth=1.2,
                linestyle="--",
                alpha=0.7,
                label=insect_label,
            )

        # Hover points for all original intervals.
        scatter = ax.scatter(
            interval_numbers,
            intervals,
            color=color,
            s=35,
            zorder=3,
        )
        scatter_objects.append((scatter, date_label, insect_id))

    if not scatter_objects:
        logger.warning("No valid interval data available to plot.")
        plt.close(fig)
        return

    # Hover annotations.
    cursor = mplcursors.cursor(
        [scatter for scatter, _, _ in scatter_objects],
        hover=mplcursors.HoverMode.Transient,
    )

    @cursor.connect("add")
    def on_add(selection):
        for scatter, date_label, insect_id in scatter_objects:
            if selection.artist is scatter:
                interval_number = int(selection.index) + 1
                selection.annotation.set_text(
                    f"Insect ID: {insect_id}\n"
                    f"Recording date: {date_label}\n"
                    f"Interval: {interval_number}\n"
                    f"Length: {selection.target[1]:.4f} s"
                )
                break

    # Legend entries explaining line styles.
    ax.plot([], [], color="black", linestyle="-", label="Filtered intervals")
    ax.plot([], [], color="black", linestyle="--", label="Outside filtered range")

    ax.set_xlabel("Interval number (backwards)")
    ax.set_ylabel("Interval length (s)")
    ax.set_title("Inter-beep intervals by insect")
    ax.set_xticks(np.arange(1, max_intervals + 1))

    # Interval 1 appears on the right.
    ax.invert_xaxis()
    ax.grid(True, alpha=0.3)

    ax.legend(
        title="Insect ID / line type",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=8,
        title_fontsize=9,
        frameon=True,
    )

    ax.set_xlim(max_intervals + 0.5, 0.5)
    ax.margins(y=0.08)

    # Leave enough room for the legend outside the plot.
    fig.subplots_adjust(right=0.78)

    plt.show()