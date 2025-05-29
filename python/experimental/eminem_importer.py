#!/usr/bin/env python3
"""
Convert pickled muon data to ROOT format (TTree or RNTuple).

This script converts pickled muon data to ROOT format, supporting both TTree and RNTuple output formats.
The input data should be a NumPy array with columns: px, py, pz, x, y, z, id, w.

Usage:
    python eminem_importer.py input_file.pkl [options]

Example:
    python eminem_importer.py muons_FullMC.pkl --output converted_data.root --format rntuple
"""

import argparse
import gzip
import json
import pickle
import sys
from pathlib import Path

import ROOT
import shipunit as u


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Convert pickled muon data to ROOT format (TTree or RNTuple)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s muons_FullMC.pkl
  %(prog)s muons_FullMC.pkl --output my_data.root
  %(prog)s muons_FullMC.pkl --format rntuple --output my_data.root
        """,
    )

    parser.add_argument(
        "input_file", help="Path to the input pickled data file (.pkl or .pkl.gz)"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="converted_from_eminem.root",
        help="Output ROOT file name (default: %(default)s)",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["ttree", "rntuple"],
        default="ttree",
        help="Output format: ttree (default) or rntuple",
    )

    parser.add_argument(
        "-t",
        "--tree-name",
        default="converted_ntuple",
        help="Name of the output tree/ntuple (default: %(default)s)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--config", help="Path to custom column configuration file (JSON format)"
    )

    parser.add_argument(
        "--list-config",
        action="store_true",
        help="Print the default column configuration and exit",
    )

    return parser.parse_args()


def load_pickled_data(input_file, verbose=False):
    """
    Load pickled data from file, handling both compressed and uncompressed files.

    Args:
        input_file (str): Path to the input pickled file
        verbose (bool): Enable verbose output

    Returns:
        numpy.ndarray: Loaded data array

    Raises:
        FileNotFoundError: If input file doesn't exist
        Exception: If file cannot be loaded or has wrong format
    """
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if verbose:
        print(f"Loading data from: {input_file}")

    try:
        # Try to load as gzipped file first
        if input_file.endswith(".gz") or input_file.endswith(".pkl.gz"):
            with gzip.open(input_file, "rb") as f:
                data = pickle.load(f)
        else:
            # Try regular pickle file
            try:
                with gzip.open(input_file, "rb") as f:
                    data = pickle.load(f)
            except gzip.BadGzipFile:
                # If it's not gzipped, load as regular pickle
                with open(input_file, "rb") as f:
                    data = pickle.load(f)

    except Exception as e:
        raise Exception(f"Failed to load pickled data: {e}")

    if verbose:
        print(f"Loaded data shape: {data.shape}")
        print(f"Data type: {data.dtype}")

    # Validate data format
    if len(data.shape) != 2 or data.shape[1] != 8:
        raise ValueError(f"Expected data with shape (N, 8), got {data.shape}")

    return data


def load_custom_config(config_path):
    """
    Load custom column configuration from JSON file.

    Args:
        config_path (str): Path to the configuration file

    Returns:
        dict: Custom configuration dictionary
    """
    try:
        with open(config_path) as f:
            custom_config = json.load(f)
        return custom_config
    except Exception as e:
        raise Exception(f"Failed to load configuration file: {e}")


def parse_custom_config_units(custom_config):
    """
    Parse custom configuration and convert string unit representations to shipunit objects.

    Args:
        custom_config (dict): Custom configuration dictionary

    Returns:
        dict: Configuration with parsed units
    """
    # Common unit mappings for shipunit
    unit_map = {
        "m": u.m,
        "cm": u.cm,
        "mm": u.mm,
        "km": u.km,
        "GeV": u.GeV,
        "MeV": u.MeV,
        "keV": u.keV,
        "eV": u.eV,
        "s": u.s,
        "ms": u.ms,
        "ns": u.ns,
        "kg": u.kg,
        "g": u.g,
        # Add more mappings as needed
    }

    parsed_config = {}
    for col_name, col_config in custom_config.items():
        parsed_col_config = col_config.copy()

        # Parse unit strings to shipunit objects
        if "unit" in col_config and isinstance(col_config["unit"], str):
            unit_str = col_config["unit"]
            if unit_str in unit_map:
                parsed_col_config["unit"] = unit_map[unit_str]
            else:
                print(
                    f"Warning: Unknown unit '{unit_str}' for column '{col_name}', ignoring unit"
                )
                parsed_col_config.pop("unit", None)

        if "offset_unit" in col_config and isinstance(col_config["offset_unit"], str):
            offset_unit_str = col_config["offset_unit"]
            if offset_unit_str in unit_map:
                parsed_col_config["offset_unit"] = unit_map[offset_unit_str]
            else:
                print(
                    f"Warning: Unknown offset unit '{offset_unit_str}' for column '{col_name}', ignoring offset unit"
                )
                parsed_col_config.pop("offset_unit", None)

        parsed_config[col_name] = parsed_col_config

    return parsed_config


def print_default_config():
    """Print the default configuration in JSON format."""
    config = get_column_config()

    # Convert to JSON-serializable format
    json_config = {}
    for col_name, col_config in config.items():
        json_col_config = {}
        for key, value in col_config.items():
            if key == "unit" or key == "offset_unit":
                # Convert units to string representation
                if value is not None:
                    # Try to get a reasonable string representation
                    if hasattr(value, "_name"):
                        json_col_config[key] = value._name
                    else:
                        json_col_config[key] = str(value)
                else:
                    json_col_config[key] = None
            else:
                json_col_config[key] = value
        json_config[col_name] = json_col_config

    print("Default column configuration:")
    print(json.dumps(json_config, indent=2))


def get_column_config(custom_config_path=None):
    """
    Define column configuration with transformations and units.

    Args:
        custom_config_path (str, optional): Path to custom configuration file

    Returns:
        dict: Column configuration dictionary
    """
    # Load custom configuration if provided
    if custom_config_path:
        try:
            custom_config = load_custom_config(custom_config_path)
            # Parse string unit representations back to shipunit objects
            return parse_custom_config_units(custom_config)
        except Exception as e:
            print(f"Warning: Could not load custom config: {e}")
            print("Using default configuration instead.")

    # Default configuration for each column
    # Each column can have: index, unit, offset, scale_factor, description
    config = {
        "px": {
            "index": 0,
            "unit": u.GeV,  # Momentum in GeV
            "description": "Momentum x-component",
        },
        "py": {
            "index": 1,
            "unit": u.GeV,  # Momentum in GeV
            "description": "Momentum y-component",
        },
        "pz": {
            "index": 2,
            "unit": u.GeV,  # Momentum in GeV
            "description": "Momentum z-component",
        },
        "x": {
            "index": 3,
            "unit": u.m,  # Position in meters
            "description": "Position x-coordinate",
        },
        "y": {
            "index": 4,
            "unit": u.m,  # Position in meters
            "description": "Position y-coordinate",
        },
        "z": {
            "index": 5,
            "unit": u.m,  # Position in meters
            "offset": -68.500,  # Apply z-offset
            "offset_unit": u.m,
            "description": "Position z-coordinate (with detector offset)",
        },
        "id": {"index": 6, "description": "Particle ID"},
        "w": {"index": 7, "description": "Weight"},
    }

    return config


def apply_column_transformation(data_column, config):
    """
    Apply transformations to a data column based on its configuration.

    Args:
        data_column (numpy.ndarray): Raw data column
        config (dict): Column configuration

    Returns:
        numpy.ndarray or shipunit quantity: Transformed data column
    """
    result = data_column.copy()

    # Apply scale factor if specified
    if "scale_factor" in config:
        result = result * config["scale_factor"]

    # Apply offset (before units if both are present)
    if "offset" in config:
        offset = config["offset"]
        if config.get("offset_unit") is not None:
            # If we have units, we need to handle the offset carefully
            if config.get("unit") is not None:
                # Both result and offset will have units
                result = result * config["unit"] + offset * config["offset_unit"]
            else:
                # Only offset has units
                result = result + offset * config["offset_unit"]
        else:
            # No units for offset
            result = result + offset

    # Apply units (if not already applied above)
    if config.get("unit") is not None and "offset" not in config:
        result = result * config["unit"]

    return result


def create_root_dataframe(data, verbose=False, custom_config_path=None):
    """
    Create ROOT RDataFrame from numpy data using configuration-driven approach.

    Args:
        data (numpy.ndarray): Input data array with columns [px, py, pz, x, y, z, id, w]
        verbose (bool): Enable verbose output
        custom_config_path (str, optional): Path to custom configuration file

    Returns:
        ROOT.RDataFrame: ROOT dataframe with the converted data
    """
    if verbose:
        print("Creating ROOT RDataFrame...")

    # Get column configuration
    column_config = get_column_config(custom_config_path)

    # Create dataframe dictionary using configuration
    df_dict = {}

    for col_name, config in column_config.items():
        # Extract raw data column
        raw_data = data[:, config["index"]]

        # Apply transformations
        transformed_data = apply_column_transformation(raw_data, config)

        # Store in dictionary
        df_dict[col_name] = transformed_data

        if verbose:
            print(f"  {col_name}: {config.get('description', 'No description')}")
            if config.get("unit"):
                print(f"    Unit: {config['unit']}")
            if config.get("offset"):
                offset_unit = config.get("offset_unit", "")
                print(f"    Offset: {config['offset']} {offset_unit}")
            if config.get("scale_factor"):
                print(f"    Scale factor: {config['scale_factor']}")

    df = ROOT.RDF.FromNumpy(df_dict)

    if verbose:
        print(f"Created RDataFrame with {df.Count().GetValue()} entries")

    return df


def save_root_file(df, output_file, tree_name, output_format, verbose=False):
    """
    Save ROOT dataframe to file in specified format.

    Args:
        df (ROOT.RDataFrame): Input dataframe
        output_file (str): Output file path
        tree_name (str): Name of the tree/ntuple
        output_format (str): Output format ('ttree' or 'rntuple')
        verbose (bool): Enable verbose output
    """
    if verbose:
        print(f"Saving to {output_file} in {output_format} format...")

    # Set up snapshot options
    opts = ROOT.RDF.RSnapshotOptions()

    if output_format == "rntuple":
        opts.fOutputFormat = ROOT.RDF.ESnapshotOutputFormat.kRNTuple
        if verbose:
            print("Using RNTuple format")
    else:
        # TTree is the default format
        if verbose:
            print("Using TTree format")

    # Save the data
    df.Snapshot(tree_name, output_file, "", opts)

    if verbose:
        print(f"Successfully saved data to {output_file}")


def main():
    """Convert pickled muon data to ROOT format (TTree or RNTuple)."""
    args = parse_arguments()

    # Handle special options
    if args.list_config:
        print_default_config()
        return

    try:
        # Load the pickled data
        data = load_pickled_data(args.input_file, args.verbose)

        # Create ROOT dataframe
        df = create_root_dataframe(data, args.verbose, args.config)

        # Save to ROOT file
        save_root_file(df, args.output, args.tree_name, args.format, args.verbose)

        print("Conversion completed successfully!")
        print(f"Input: {args.input_file}")
        print(f"Output: {args.output} ({args.format} format)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
