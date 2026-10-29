import logging
import pandas as pd

logger = logging.getLogger(__name__)

def display_dataset_structure(data):

    for dataset_id, entry in data.items():

        logger.info("Dataset %s", dataset_id)
        logger.info("  Available sections: %s", list(entry.keys()))

        if "metadata" in entry:
            logger.info(
                "  Metadata columns: %s",
                list(entry["metadata"].keys()),
            )

        if "raven" in entry:
            logger.info(
                "  Raven columns: %s",
                list(entry["raven"].columns),
            )

        if "additional_parameters" in entry:
            logger.info(
                "  Additional parameters: %s",
                list(entry["additional_parameters"].keys()),
            )

def display_raven_values(data, config, columns, types, col_space=10):

    selection_column = config["raven"]["columns"]["selection"]
    age_column = config["metadata"]["columns"]["age"]

    rows = []

    for dataset_key, entry in data.items():

        raven = entry["raven"]
        metadata = entry["metadata"]

        # Check requested columns
        missing_columns = [
            column for column in columns
            if column not in raven.columns
        ]

        if missing_columns:
            logger.warning(
                f"WARNING: {dataset_key}: "
                f"missing columns: {missing_columns}"
            )
            continue

        # Check selection column
        if selection_column not in raven.columns:
            logger.warning(
                f"WARNING: {dataset_key}: "
                f"selection column '{selection_column}' does not exist."
            )
            continue

        # Check requested types
        present_types = set(
            raven[selection_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        missing_types = [
            type_name for type_name in types
            if type_name not in present_types
        ]

        if missing_types:
            logger.warning(
                f"WARNING: {dataset_key}: "
                f"missing types: {missing_types}"
            )

        # Keep only requested types
        selected = raven[
            raven[selection_column]
            .astype(str)
            .str.strip()
            .isin(types)
        ].copy()

        # Add dataset information
        selected.insert(0, "Age", metadata[age_column])
        selected.insert(0, "Dataset ID", dataset_key)

        rows.append(
            selected[
                ["Dataset ID", "Age", selection_column] + columns
            ]
        )

    # Combine everything into one table
    if rows:
        table = pd.concat(rows, ignore_index=True)

        print("\n")
        print(table.to_string(index=False, col_space=col_space))