from pathlib import Path
from datetime import datetime
from src.logger import ColoredFormatter

import logging
import pandas as pd

logger = logging.getLogger(__name__)

def load_dataset(config):
    """
    Load metadata and Raven Pro selection files.

    The function:

    1. Reads the metadata CSV.
    2. Selects recordings where ``Done`` matches the configured
       value.
    3. Builds the expected Raven filename for each recording.
    4. Checks that the Raven file exists.
    5. Reads the Raven file into memory.
    6. Checks that all required Raven selections are present.

    Parameters
    ----------
    config : dict
        Analysis configuration.

    Returns
    -------
    dict
        Dataset containing the metadata and Raven data for each
        recording.

    Raises
    ------
    FileNotFoundError
        If the metadata file or an expected Raven file does not exist.

    ValueError
        If required columns or Raven selections are missing.
    """

    # =========================================================
    # CONFIGURATION
    # =========================================================

    metadata_file = Path(config["data"]["metadata_file"])
    
    recordings_directory = Path(
        config["data"]["recordings_directory"]
    )

    metadata_columns = config["metadata"]["columns"]
    raven_columns = config["raven"]["columns"]

    id_column = metadata_columns["id"]
    date_column = metadata_columns["date"]
    temperature_column = metadata_columns["temperature"]
    done_column = metadata_columns["done"]

    selection_column = raven_columns["selection"]

    done_value = str(
        config["metadata"]["done_value"]
    ).strip().lower()

    required_selections = config["raven"]["required_selections"]
    
    filename_config = config["raven"]["filename"] 
    
    filename_pattern_template = filename_config["pattern"] 
    filename_date_format = filename_config["date_format"] 

    # Metadata dates are currently expected as DD/MM/YYYY. 
    metadata_date_format = "%d/%m/%Y"

    # =========================================================
    # CHECK PATHS
    # =========================================================

    if not metadata_file.is_file():
        raise FileNotFoundError(
            f"Metadata file not found: {metadata_file}",
            f"Absolute path: {metadata_file.resolve()}"
        )

    if not recordings_directory.is_dir():
        raise FileNotFoundError(
            f"Recordings directory not found: "
            f"{recordings_directory}",
            f"Absolute path: {recordings_directory.resolve()}"
        )

    # # =========================================================
    # # DEBUG - RECORDINGS DIRECTORY
    # # =========================================================

    # print("\n" + "=" * 60)
    # print("RAVEN FILE DEBUG")
    # print("=" * 60)

    # print(f"Current working directory:")
    # print(f"  {Path.cwd()}")

    # print(f"\nRecordings directory:")
    # print(f"  {recordings_directory}")

    # print(f"\nAbsolute recordings directory:")
    # print(f"  {recordings_directory.resolve()}")

    # print(f"\nDirectory exists:")
    # print(f"  {recordings_directory.is_dir()}")

    # print("\nFiles Python sees in recordings directory:")

    # files_in_directory = sorted(
    #     recordings_directory.iterdir()
    # )

    # if not files_in_directory:
    #     print("  *** DIRECTORY IS EMPTY ***")
    # else:
    #     for path in files_in_directory:
    #         print(f"  {repr(path.name)}")

    # print("=" * 60 + "\n")

    # =========================================================
    # READ METADATA
    # =========================================================

    try:
        metadata = pd.read_csv(
            metadata_file,
            dtype=str,
        )
    except Exception as exc:
        logger.warning(
            "Could not read metadata file %s: %s",
            metadata_file,
            exc,
        )
        return {}

    metadata.columns = metadata.columns.str.strip()

    # =========================================================
    # VALIDATE METADATA COLUMNS
    # =========================================================

    required_metadata_columns = {
        id_column,
        date_column,
        done_column,
    }

    missing_columns = (
        required_metadata_columns - set(metadata.columns)
    )

    if missing_columns:
        logger.warning(
            "Metadata is missing required columns: %s",
            sorted(missing_columns),
        )

    if id_column not in metadata.columns: 
        logger.warning( 
            "ID column %r is missing. Cannot identify recordings.", 
            id_column, 
        ) 
        return {} 

    if date_column not in metadata.columns: 
        logger.warning( 
            "Date column %r is missing. Cannot identify recordings.", 
            date_column, 
        ) 
        return {} 

    if temperature_column not in metadata.columns: 
        logger.warning( 
            "Temperature column %r is missing. Cannot identify recordings.", 
            temperature_column, 
        ) 
        return {} 

    if done_column not in metadata.columns: 
        logger.warning( 
            "Done column %r is missing. Cannot determine " 
            "which recordings should be analyzed.", 
        done_column, ) 

        return {}

    # =========================================================
    # SELECT RECORDINGS TO ANALYZE
    # =========================================================

    done_mask = (
        metadata[done_column]
        .fillna("")
        .str.strip()
        .str.lower()
        == done_value
    )

    signals = metadata.loc[done_mask].copy()

    if signals.empty:
        raise ValueError(
            f"No recordings found where "
            f"{done_column!r} == {done_value!r}"
        )

    logger.info(
        "Found %d recording(s) marked for analysis.",
        len(signals),
    )

    # =========================================================
    # LOAD RECORDINGS
    # =========================================================

    dataset = {}

    for _, row in signals.iterrows():

        # -----------------------------------------------------
        # READ METADATA
        # -----------------------------------------------------

        recording_id = str(row[id_column]).strip()

        recording_date = str(row[date_column]).strip()

        dataset_key = f"{recording_id}_{recording_date.replace('/', '')[-6:]}"


        if not recording_id or recording_id.lower() == "nan":
            logger.warning(
                "Skipping recording with missing ID."
            )
            continue

        if not recording_date or recording_date.lower() == "nan":
            logger.warning(
                "Skipping recording %r because the date is missing.",
                recording_id,
            )
            continue

        # -----------------------------------------------------
        # CREATE DATASET KEY
        # -----------------------------------------------------

        try: 
            parsed_date = datetime.strptime( 
                recording_date, 
                metadata_date_format, 
                )

        except ValueError:
            logger.warning(
                "Skipping recording %r: invalid date %r. "
                "Expected format %r.",
                recording_id,
                recording_date,
                metadata_date_format,
            )
            continue

        dataset_key = ( 
            f"{recording_id}_" 
            f"{parsed_date.strftime('%d%m%y')}" 
            )

        # ----------------------------------------------------- 
        # BUILD RAVEN FILENAME 
        # ----------------------------------------------------- 

        filename_date = parsed_date.strftime( 
            filename_date_format 
        ) 

        filename_pattern = ( 
            filename_pattern_template.format( 
                id=recording_id, 
                date=filename_date, 
            ) 
        )

        # # -----------------------------------------------------
        # # DEBUG - FILE SEARCH
        # # -----------------------------------------------------

        # print("-" * 60)
        # print(f"Recording ID:       {recording_id}")
        # print(f"Metadata date:      {recording_date}")
        # print(f"Filename date:      {filename_date}")
        # print(f"Search directory:   {recordings_directory.resolve()}")
        # print(f"Search pattern:     {filename_pattern}")

        # # Show files that start with the expected ID/date.
        # expected_prefix = (
        #     f"{recording_id}_{filename_date}-"
        # )

        # possible_files = [
        #     path
        #     for path in files_in_directory
        #     if path.name.startswith(expected_prefix)
        # ]

        # print(f"Expected prefix:    {expected_prefix}")
        # print("Possible matching files:")

        # if possible_files:
        #     for path in possible_files:
        #         print(f"  {repr(path.name)}")
        # else:
        #     print("  *** NONE ***")


        # -----------------------------------------------------
        # FIND FILE
        # -----------------------------------------------------

        matching_files = sorted(
            recordings_directory.glob(filename_pattern)
        )

        # -----------------------------------------------------
        # CHECK FILE EXISTS
        # -----------------------------------------------------

        if not matching_files: 
            logger.warning( 
                "Dataset %s: Raven file missing. " 
                "Expected pattern: %s", 
                dataset_key, 
                filename_pattern, 
            ) 

            continue

        if len(matching_files) > 1:

            logger.warning(
                "Dataset %s: multiple Raven files found:",
                dataset_key,
            )

            for path in matching_files:
                logger.warning(
                    "  %s",
                    path,
                )

            # Skip this recording because it is ambiguous.
            continue

        raven_file = matching_files[0]

        # logger.info( 
        #     "Loading dataset %s from %s", 
        #     dataset_key, 
        #     raven_file.name, )

        # -----------------------------------------------------
        # READ RAVEN FILE
        # -----------------------------------------------------

        try:
            raven_data = pd.read_csv(
                raven_file,
                sep="\t",
            )

        except Exception as exc:
            logger.warning(
                "Could not read Raven file %s: %s",
                raven_file,
                exc,
            )
            continue

        raven_data.columns = (
            raven_data.columns
            .str.strip()
        )


        # -----------------------------------------------------
        # VALIDATE RAVEN COLUMNS
        # -----------------------------------------------------


        if selection_column not in raven_data.columns:

            logger.warning(
                "Raven file %s is missing the configured "
                "selection column %r.",
                dataset_key,
                selection_column,
            )

            continue

        # # -----------------------------------------------------
        # # CLEAN ANALYSIS PARAMETERS
        # # -----------------------------------------------------

        # analysis_parameters = config["analysis"]["parameters"]

        # for parameter in analysis_parameters:

        #     if parameter not in raven_data.columns:
        #         continue

        #     raven_data[parameter] = pd.to_numeric(
        #         raven_data[parameter],
        #         errors="coerce",
        #     )

        # # -----------------------------------------------------
        # # DEBUG - CHECK CLEANED RAVEN DATA
        # # -----------------------------------------------------

        # logger.info(
        #     "Dataset %s: Raven data after cleaning:",
        #     dataset_key,
        # )

        # debug_columns = [
        #     selection_column,
        #     "View",
        #     "Peak Freq (Hz)",
        #     "Center Freq (Hz)",
        #     "Freq 75% (Hz)",
        # ]

        # debug_columns = [
        #     column
        #     for column in debug_columns
        #     if column in raven_data.columns
        # ]

        # logger.info(
        #     "\n%s",
        #     raven_data[debug_columns].to_string(index=False),
        # )


        # -----------------------------------------------------
        # CHECK REQUIRED SELECTIONS
        # -----------------------------------------------------

        present_selections = set(
            raven_data[selection_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        missing_selections = [
            selection
            for selection in required_selections
            if selection not in present_selections
        ]

        if missing_selections:

            logger.warning(
                "Dattaset %s is missing "
                "selections: %s",
                dataset_key,
                missing_selections,
            )

        # -----------------------------------------------------
        # STORE RECORDING
        # -----------------------------------------------------

        dataset[dataset_key] = {
            "metadata": row.to_dict(),
            "raven_file": raven_file,
            "raven": raven_data,
        }

    # =========================================================
    # SUMMARY
    # =========================================================

    logger.info( 
        "Successfully loaded %d dataset entries.", 
        len(dataset), 
    ) 

    logger.info( 
        "Dataset keys: %s", 
        list(dataset.keys()), 
    ) 

    # logger.info(
    #     "Number of observations: %d",
    #     len(dataset),
    # )

    # logger.info(
    #     "Number of insects: %d",
    #     dataset["ID"].nunique(),
    # )



    return dataset
