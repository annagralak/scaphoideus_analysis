import logging

from config import ANALYSIS_CONFIG
from src.io import load_dataset
from src.display import display_dataset_structure, display_raven_values
from src.logger import ColoredFormatter
from src.variability import add_parameter_variability
from src.rhytmic_analysis import add_rhythmic_analysis
from src.statistics import run_analysis
# from src.reporting import generate_report

# Choose logging level here
LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.WARNING

def setup_logger():
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter("%(levelname)s: %(message)s")
    )

    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

def main():

    # Logging
    setup_logger()

    # Load
    data = load_dataset(ANALYSIS_CONFIG)

    # Display data
    # display_dataset_structure(data)

    # display_raven_values(
    #     data,
    #     ANALYSIS_CONFIG,
    #     columns=["Peak Freq (Hz)"],
    #     types=["whole", "five"],
    # )

    # Variability of Raven parameters
    # This is still calculated from b1-b5
    data = add_parameter_variability(data)

    # Adding rhytmic parameters
    data = add_rhythmic_analysis(data)

    # # Statistical analysis
    results = run_analysis(data)

    # Save results
    # generate_report(results)


if __name__ == "__main__":
    main()
