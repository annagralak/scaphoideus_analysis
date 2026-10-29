# *Scaphoideus titanus* - Signal analysis

## Overview

This project analyzes vibrational recordings of *Scaphoideus titanus* using measurements exported from Raven Pro. It combines signal parameters with insect metadata, including age, recording date, and temperature, to investigate relationships between acoustic characteristics and biological or environmental factors.

The analysis includes:

- Acoustic parameter analysis for selected parts of each recording.
- Measurements of variation in acoustic parameters.
- Analysis of beep timing and rhythmic characteristics.
- Pearson correlation analysis.
- Generalized Additive Mixed Model (GAMM) analysis to investigate relationships between acoustic parameters and age or temperature.
- Visualization of observations and fitted statistical relationships.

The project is designed to be configurable through `config.py`, without needing to modify the main analysis code for most changes.

## Project structure

The project expects the input data to be organized as follows:

```text
project/
├── main.py
├── config.py
├── data/
│   ├── metadata.csv
│   └── selections/
│       ├── M6_0107_25-1.Table.1.selections.txt
│       └── ...
└── src/
    ├── ...
```

The `src/` directory contains the analysis, data processing, statistical modelling, and plotting modules.

- `main.py` starts the analysis.
- `config.py` contains the input paths and analysis settings.
- `data/metadata.csv` contains insect metadata.
- `data/selections/` contains the Raven Pro selection tables exported as TXT files.

## Data processing

### 1. Marking acoustic signals in Raven Pro

Each acoustic recording is analyzed in Raven Pro by marking selections corresponding to different parts of the signal.

The current selection strategy includes the following:

| Selection | Description |
|---|---|
| `whole` | The entire signal. |
| `five` | The last five beeps considered together as one selection. |
| b1, b2, b3, etc. | Individual intervals counted backwards from the end of the signal. b1 is the last interval, b2 is the second-to-last interval, and so on. Additional intervals are being annotated progressively. |

The exact selection names used by the script are configured in `config.py`.

The purpose of these selections is to compare acoustic characteristics across the entire signal, a standardized portion at the end of the signal, and individual intervals.

Annotation of all individual intervals is an ongoing process. As more intervals are marked, additional selections can be included in the analysis by updating the configuration.

### 2. Measuring intervals from the end of the signal

Individual intervals are annotated by counting backwards from the end of the signal rather than from the beginning. This approach is based on the observation that the beeps tend to become more rhythmic towards the end of a signal. Starting from the end therefore makes it easier to identify a relatively stable sequence of intervals for analysis.

The last interval is labelled b1, the second-to-last b2, and so on. This creates a consistent reference point across recordings, even when the total number of beeps or the overall signal duration differs.

Using this backward-counting approach also makes it easier to organize and flatten the data into a consistent structure, so that corresponding intervals can be compared across recordings. The annotation of additional intervals is ongoing.

### 3. Exporting measurements from Raven Pro

After the selections have been marked, the selection table is exported from Raven Pro as a TXT file containing the calculated acoustic parameters.

The script reads these exported tables and extracts the parameters associated with the configured selection types.

The selection tables are expected to follow a filename pattern defined in `config.py`:

```text
{id}_{date}-*.Table.1.selections.txt
```

For example:

```text
M6_0107_25-1.Table.1.selections.txt
```

The filename contains the insect ID and recording date, which are used to match the file to the corresponding metadata entry.

### 4. Metadata in the CSV file

The metadata file, `data/metadata.csv`, contains information associated with each recording.

The default columns are:

| Column | Description |
|---|---|
| `ID` | Insect identifier. |
| `Age` | Age of the insect at the time relevant to the recording. |
| `Date` | Recording date. |
| `Temperature` | Temperature associated with the recording. |
| `Done` | Indicates whether the recording should be included in the analysis. |

Only recordings whose `Done` value matches the configured `done_value` (default: `yes`) are intended to be included.

For each eligible metadata entry, the script searches for the corresponding Raven Pro selection table using the insect ID and recording date. It then combines the metadata with the acoustic measurements extracted from the selection table.

This creates the data used for statistical analysis.

## Statistical analysis

### 1. Acoustic parameters

The analysis can be configured to examine different acoustic measurements exported from Raven Pro.

Examples include:

- Peak frequency.
- Center frequency.
- Frequency bandwidth.
- Signal duration.
- Relative timing measurements.
- Average power density.
- Aggregate entropy.

The available parameters are specified in `config.py`. The script can also analyze variability measures and rhythmic characteristics, such as the number of beeps, mean interval, minimum interval, and rhythmic coefficient.

The exact measurements included in a run depend on the active configuration.

### 2. Pearson correlation

Pearson correlation analysis is used to assess the strength and direction of a linear relationship between two variables.

The correlation coefficient indicates whether the relationship is positive or negative and how strong the linear association is. The associated significance test assesses whether the observed correlation provides evidence against a zero correlation.

The significance threshold is configurable in `config.py` and defaults to `0.05`.

Plotting settings can control whether all correlations or only statistically significant correlations are displayed.

### 3. Generalized Additive Mixed Models (GAMMs)

GAMMs are used to investigate how acoustic parameters relate to age or temperature while accounting for repeated observations from the same insect.

Unlike a simple linear regression, a GAMM can model a nonlinear relationship between a predictor and the response. This is useful when acoustic characteristics may change in a curved or otherwise non-linear way as an insect ages or as temperature changes.

The model includes:

- **Response variable:** The acoustic parameter or rhythmic measurement being investigated.
- **Main predictor:** Age or temperature.
- **Optional covariates:** Temperature, age, and recording date, depending on the configured analysis.
- **Random effects:** Insect identity, to account for multiple observations from the same insect.

The main predictor is represented using spline terms. These spline terms work together to form one fitted curve, allowing the model to represent nonlinear patterns.

#### Accounting for repeated measurements

Several observations may come from the same insect, so the observations cannot necessarily be treated as fully independent.

The mixed-model structure accounts for differences between insects through insect-specific random effects. Depending on the model configuration, this can include differences in baseline response and differences in the relationship between the predictor and response.

#### Including covariates

Age, temperature, and recording date can be included as covariates when appropriate.

For example, when investigating the relationship between temperature and rhythmic coefficient, age and recording date can be included to account for their potential associations with the response.

The purpose is to estimate the relationship with the main predictor while accounting for the other variables included in the model.

#### Interpreting the results

The model summary includes coefficient estimates, standard errors, p-values, confidence intervals, and random-effect estimates.

For spline-based predictors, individual spline coefficients should not be interpreted as separate biological effects. The spline terms jointly describe the fitted relationship. An overall test of the spline terms is needed to assess evidence for an association between the main predictor and the response.

A p-value below the configured significance threshold is commonly treated as evidence against the relevant null hypothesis. A p-value above the threshold does not prove that an effect is absent.

Plots help interpret the fitted relationship and compare the model's predictions with the observed data.

## Running the analysis

### Requirements

Use a Python environment with the dependencies required by the project installed.

### Start the script

From the project root directory, run:

```bash
python main.py
```

The script loads the configuration, reads the metadata, locates the corresponding Raven Pro selection tables, processes the measurements, and runs the configured analyses.

Plot display and other plotting behavior depend on the settings in `config.py`.

## Configuration

All primary analysis settings are defined in `config.py`, inside the `ANALYSIS_CONFIG` dictionary.

### 1. Input data paths

```python
"data": {
    "metadata_file": Path("data/metadata.csv"),
    "recordings_directory": Path("data/selections"),
},
```

Change these paths if the metadata file or Raven Pro exports are stored elsewhere.

### 2. Metadata columns and inclusion criteria

```python
"metadata": {
    "columns": {
        "id": "ID",
        "date": "Date",
        "age": "Age",
        "temperature": "Temperature",
        "done": "Done",
    },
    "done_value": "yes",
},
```

Update the column names if the CSV uses different headers. Change `done_value` to match the value used to mark recordings for inclusion.

### 3. Raven Pro selection names and filenames

```python
"raven": {
    "columns": {
        "selection": "Type",
    },
    "required_selections": [
        "whole",
        "five",
        "b1",
        "b2",
        "b3",
        "b4",
        "b5",
    ],
    "filename": {
        "pattern": "{id}_{date}-*.Table.1.selections.txt",
        "date_format": "%d%m%y",
    },
},
```

This section defines the selection column, expected selection names, filename pattern, and date format.

The required selections should be kept consistent with the annotations actually present in the Raven Pro exports. If additional intervals are annotated, update the selection list as needed.

### 4. Selecting parameters and analyses

The `analysis` section specifies which selections, acoustic parameters, variability measurements, and rhythmic measurements should be analyzed.

For example:

```python
"analysis": {
    "selections": [
        "b5",
    ],
    "parameters": [
        "Peak Freq (Hz)",
        "Dur 90% (s)",
    ],
    "variability": [
        "Peak Freq (Hz) Variability",
    ],
    "rhytmic_analysis": [
        "Number of Beeps",
        "Mean Interval",
        "Minimum Interval",
        "Rhythmic Coefficient",
    ],
},
```

These names must correspond to the parameter names recognized by the project and the values available in the exported data.

To analyze a different interval, add or replace the selection name. To analyze additional acoustic measurements, add their names to the appropriate list.

### 5. Configuring GAMM models

The `analysis_groups` list determines which statistical models are run.

Each configuration specifies:

- `predictor`: The main predictor, `Age` or `Temperature`.
- `include_age`: Whether Age is included as a covariate when it is not already the main predictor.
- `include_temperature`: Whether Temperature is included as a covariate when it is not already the main predictor.
- `include_date`: Whether recording date is included as a covariate.

For example:

```python
"analysis_groups": [
    {
        "predictor": "Age",
        "include_age": False,
        "include_temperature": True,
        "include_date": False,
    },
    {
        "predictor": "Temperature",
        "include_age": True,
        "include_temperature": False,
        "include_date": False,
    },
],
```

The first configuration investigates Age while accounting for Temperature. The second investigates Temperature while accounting for Age.

To include recording date as an additional covariate, set `include_date` to `True`.

Only configurations listed in `analysis_groups` are intended to be run. Add, remove, or uncomment configurations to change the models being fitted.

### 6. Plotting settings

```python
"plotting": {
    "show_plot": True,
    "show_only_significant": True,
    "show_values": True,
    "show_regression_line": True,
    "show_confidence_interval": True,
},
```

These options control the display of plots, including whether plots are shown, whether only significant correlations are displayed, whether observation values are annotated, and whether regression lines and confidence intervals are included.

### 7. Significance threshold

```python
"statistics": {
    "significance_level": 0.05,
},
```

This setting defines the significance threshold used by the correlation analysis. It does not automatically imply that every statistical procedure in the project uses the same threshold.

## Notes and limitations

- Raven Pro selection names and exported parameter names must match the configuration and the expected data format.
- Each recording must be identifiable through the metadata and filename matching rules.
- The completeness of interval-based analyses depends on how many individual intervals have been annotated.
- Some statistical models may be skipped or fail to fit if there are too few observations or too few insects with usable data.
- GAMM results should be interpreted using the fitted curve, appropriate overall tests, confidence intervals, and the study design—not solely by examining individual spline coefficients.
- Some GAMM models may fail to converge, meaning the model cannot reliably estimate the fitted relationship from the available data. In these cases, the plot displays the observed data points without a fitted curve. This does not necessarily mean that no relationship exists; it means the model could not produce a reliable fit for that dataset.
- Configuration changes should be checked against the actual metadata and Raven Pro exports before running a full analysis.

