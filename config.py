from pathlib import Path


ANALYSIS_CONFIG = {

    # =====================================================
    # DATA
    # =====================================================

    "data": {

        # Excel file containing metadata
        "metadata_file": Path("data/metadata.csv"),

        # Directory containing Raven Pro TXT files
        "recordings_directory": Path("data/selections"),
    },


    # =====================================================
    # METADATA
    # =====================================================

    "metadata": {

        # Column names in the Excel metadata file
        "columns": {
            "id": "ID",
            "date": "Date",
            "age": "Age",
            "temperature": "Temperature",
            "done": "Done",
        },

        # Value in the "Done" column indicating that
        # the recording should be included in the analysis.
        "done_value": "yes",
    },


    # =====================================================
    # RAVEN PRO
    # =====================================================

    "raven": {

    	"columns": {
    		"selection": "Type",
		},

        # Raven Pro selections that are expected
        # for every recording.
        "required_selections": [
            # "pb",
            "whole",
            "five",
            "b1",
            "b2",
            "b3",
            "b4",
            "b5",
        ],

        # Example:
        #
        # M6_0107_25-1.Table.1.selections.txt
        #
        # The filename starts with:
        #     ID_DATE
        #

		"filename": {
    		"pattern": "{id}_{date}-*.Table.1.selections.txt",
    		"date_format": "%d%m%y",
		},
    },


    # =====================================================
    # ANALYSIS
    # =====================================================
    "analysis": {

        "selections": [
            "whole", 
            "five", 
            "b1",
            "b2", 
            "b3", 
            "b4", 
            "b5",
            ],

        "parameters": [
            "Peak Freq (Hz)",
            "Center Freq (Hz)",
            "Freq 75% (Hz)",
            "Freq 95% (Hz)",
            "BW 50% (Hz)",
            "BW 90% (Hz)",
            # "Peak Freq Contour (Hz)",
            # "PFC Slope (Hz/ms)",
            "Dur 90% (s)",
            "Center Time Rel.",
            "Peak Time Relative",
            "Avg Power Density (dB FS/Hz)",
            "Agg Entropy (bits)",
            # "SNR NIST Quick (dB)",
            ],

        "variability": [
            "Peak Freq (Hz) Variability", 
            "Center Freq (Hz) Variability",
            "Freq 75% (Hz) Variability",
            "Freq 95% (Hz) Variability",
            "BW 50% (Hz) Variability",
            "BW 90% (Hz) Variability",
            "Dur 90% (s) Variability",
            "Center Time Rel. Variability",
            "Peak Time Relative Variability",
            "Avg Power Density (dB FS/Hz) Variability",
            "Agg Entropy (bits) Variability",
            ],

        "rhytmic_analysis": [
            "Number of Beeps",
            "Mean Interval",
            "Minimum Interval",
            "Rhythmic Coefficient",
            "Interval List",
            "Filtered Interval List"
        ],

        # All legal analysis configurations below
        "analysis_groups": [
            # 1. Age predictor; no additional covariates
            {
                "predictor": "Age",
                "include_age": False,
                "include_temperature": False,
                "include_date": False,
            },

            # 2. Age predictor; Temperature covariate
            {
                "predictor": "Age",
                "include_age": False,
                "include_temperature": True,
                "include_date": False,
            },

            # 3. Age predictor; Date covariate
            {
                "predictor": "Age",
                "include_age": False,
                "include_temperature": False,
                "include_date": True,
            },

            # 4. Age predictor; Temperature and Date covariates
            {
                "predictor": "Age",
                "include_age": False,
                "include_temperature": True,
                "include_date": True,
            },

            # 5. Temperature predictor; no additional covariates
            {
                "predictor": "Temperature",
                "include_age": False,
                "include_temperature": False,
                "include_date": False,
            },

            # 6. Temperature predictor; Age covariate
            {
                "predictor": "Temperature",
                "include_age": True,
                "include_temperature": False,
                "include_date": False,
            },

            # 7. Temperature predictor; Date covariate
            {
                "predictor": "Temperature",
                "include_age": False,
                "include_temperature": False,
                "include_date": True,
            },

            # 8. Temperature predictor; Age and Date covariates
            {
                "predictor": "Temperature",
                "include_age": True,
                "include_temperature": False,
                "include_date": True,
            },
        ]
    },


    # =====================================================
    # STATISTICS
    # =====================================================
    #
    # Statistical settings will be added later.
    #

    "statistics": {

        # Pearson correlation significance threshold.
        "significance_level": 0.05,
    },

    # =====================================================
    # PLOTTING
    # =====================================================
    #
    # Settings controlling how plots are displayed.
    #

    "plotting": {

        # If the plots are displayed at all
        "show_plot": True,

        # If True, only plot statistically significant
        # correlations.
        # If False, plot all correlations.
        "show_only_significant": True,

        # If True, display the parameter value next to
        # each observation.
        "show_values": True,

        # If True, display the linear regression line.
        "show_regression_line": True,

        # If True, display the 95% confidence interval
        # around the regression line.
        "show_confidence_interval": True,
        },
}