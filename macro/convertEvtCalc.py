"""Convert files from EventCalc to ROOT format."""

import sys
import os
from argparse import ArgumentParser

import numpy as np
import ROOT as r


def parse_file(infile):
    """
    Parse the given text file and extracts process type, sample points, and variables.

    Parameters:
    infile (str): Path to the input text file.

    Returns:
    tuple: A tuple containing process type (str), sample points (int), and a list of numpy arrays for each variable.
    """
    try:
        with open(infile, "r") as file:
            lines = file.readlines()

        parsed_data = []
        current_block = []
        process_type = None
        sampled_points = None

        for line in lines:
            if line.startswith("#<"):
                if current_block:
                    data = np.loadtxt(current_block)
                    variables = [data[:, i] for i in range(data.shape[1])]
                    current_block = []
                    header = line.strip()
                    process_type = header.split(";")[0].split("=")[1]
                    # print(f'Process type: {process_type}')
                    sampled_points = int(header.split(";")[1].split("=")[1][:-1])
                    # print(f'Sampled points: {sampled_points}')
                    parsed_data.append((process_type, sampled_points, variables))
            else:
                current_block.append(line.strip())

        if current_block:
            data = np.loadtxt(current_block)
            variables = [data[:, i] for i in range(data.shape[1])]
            parsed_data.append((process_type, sampled_points, variables))

        return parsed_data

    except FileNotFoundError:
        print(f"- convertEvtCalc - Error: The file {infile} was not found.")
        return None, None, None
    except Exception as e:
        print(f"- convertEvtCalc - An error occurred: {e}")
        return None, None, None


def check_consistency_infile(nvars, ncols):
    """
    Check the consistency between number of columns in the input file (ncols) and variables (nvars).

    Parameters:
    nvars, ncols (int or float): The value to be checked. Must be equal.

    """
    if nvars != ncols:
        raise ValueError("Nr of variables does not match input file.")
    return


def convert_file(infile, outdir):
    """
    Create a ROOT file with a TTree containing the variables from the parsed input text file.

    Parameters:
    infile (str): Path to the input text file.
    outdir (str): Name of the output directory, the filename will be the same
                  as inputfile with the .dat replaced with .root.
    """
    vars_names = [
        "px_llp",
        "py_llp",
        "pz_llp",
        "e_llp",
        "mass_llp",
        "pdg_llp",
        "decay_prob",
        "vx",
        "vy",
        "vz",
    ]
    vars_names += [
        "px_prod1",
        "py_prod1",
        "pz_prod1",
        "e_prod1",
        "mass_prod1",
        "pdg_prod1",
        "charge_prod1",
        "stability_prod1",
    ]
    vars_names += [
        "px_prod2",
        "py_prod2",
        "pz_prod2",
        "e_prod2",
        "mass_prod2",
        "pdg_prod2",
        "charge_prod2",
        "stability_prod2",
    ]
    vars_names += [
        "px_prod3",
        "py_prod3",
        "pz_prod3",
        "e_prod3",
        "mass_prod3",
        "pdg_prod3",
        "charge_prod3",
        "stability_prod3",
    ]

    fname = infile.split("/")[-1]
    command = f"cp {infile} {outdir}/{fname}"

    if os.path.isfile(f"{outdir}/{fname}"):
        print(f"Warning: The file {outdir}/{fname} already exists.")
    else:
        os.system(command)

    infile = f"{outdir}/{fname}"
    parsed_data = parse_file(infile)
    outfile = infile.split(".dat")[0] + ".root"

    try:
        check_consistency_infile(nvars=len(vars_names), ncols=len(parsed_data[0][2]))
    except ValueError as e:
        print(f"- convertEvtCalc - Error: {e}")
        sys.exit(1)

    if parsed_data:
        root_file = r.TFile.Open(outfile, "RECREATE")

        tree = r.TTree("LLP_tree", "LLP_tree")

        branch_i = {}
        branch_f = {}
        for var in vars_names:
            if "pdg_" in var:
                branch_i[var] = np.zeros(1, dtype=int)
                tree.Branch(var, branch_i[var], f"{var}/I")
            else:
                branch_f[var] = np.zeros(1, dtype=float)
                tree.Branch(var, branch_f[var], f"{var}/D")

        for pt, sp, vars in parsed_data:
            for row in zip(*vars):
                for i, value in enumerate(row):
                    if i < len(vars_names):
                        if "pdg_" in vars_names[i]:
                            branch_i[vars_names[i]][0] = value
                        else:
                            branch_f[vars_names[i]][0] = value
                tree.Fill()

        tree.Write()
        root_file.Close()
        print(f"- convertEvtCalc - ROOT file '{outfile}' created successfully.")
        return outfile


def main():
    """Convert files from EventCalc to ROOT format."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "-f",
        "--inputfile",
        help="""Simulation results to use as input."""
        """Supports retrieving file from EOS via the XRootD protocol.""",
        required=True,
    )
    parser.add_argument(
        "-o", "--outputdir", help="""Output directory, must exist.""", default="."
    )
    args = parser.parse_args()
    print(f"Opening input file for conversion: {args.inputfile}")
    if not os.path.isfile(args.inputfile):
        raise FileNotFoundError("EvtCalc: input .dat file does not exist")
    if not os.path.isdir(args.outputdir):
        print(
            f"Warning: The specified directory {args.outputdir} does not exist. Creating it now."
        )
        command = f"mkdir {args.outputdir}"
        os.system(command)
    outputfile = convert_file(infile=args.inputfile, outdir=args.outputdir)
    print(f"{args.inputfile} successfully converted to {outputfile}.")


if __name__ == "__main__":
    main()
