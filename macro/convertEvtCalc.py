import sys

import numpy as np
import ROOT as r


def parse_file(infile):
    """
    Parses the given text file and extracts process type, sample points, and variables.

    Parameters:
    infile (str): Path to the input text file.

    Returns:
    tuple: A tuple containing process type (str), sample points (int), and a list of numpy arrays for each variable.
    """

    try:
        with open(infile, 'r') as file:
            lines = file.readlines()

        parsed_data    = []
        current_block  = []
        process_type   = None
        sampled_points = None

        for line in lines:
            if line.startswith('#<'):
                if current_block:
                    data = np.loadtxt(current_block)
                    variables = [data[:, i] for i in range(data.shape[1])]
                    current_block = []
                    header       = line.strip()
                    process_type = header.split(';')[0].split('=')[1]
                    print(f'Process type: {process_type}')
                    sampled_points = int(header.split(';')[1].split('=')[1][:-1])
                    print(f'Sampled points: {sampled_points}')
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
    if nvars!=ncols:
        raise ValueError("Nr of variables does not match input file.")
    return


def convert_file(infile, outfile):
    """
    Creates a ROOT file with a TTree containing the variables from the parsed input text file.

    Parameters:
    infile (str): Path to the input text file.
    outfile (str): Name of the output ROOT file.
    """

    vars_names  = ['px_llp', 'py_llp', 'pz_llp', 'e_llp', 'mass_llp', 'pdg_lpp', 'decay_prob', 'vx', 'vy', 'vz']
    vars_names += ['px_prod1', 'py_prod1', 'pz_prod1', 'e_prod1', 'mass_prod1', 'pdg_prod1', 'charge_prod1', 'stability_prod1']
    vars_names += ['px_prod2', 'py_prod2', 'pz_prod2', 'e_prod2', 'mass_prod2', 'pdg_prod2', 'charge_prod2', 'stability_prod2']
    vars_names += ['px_prod3', 'py_prod3', 'pz_prod3', 'e_prod3', 'mass_prod3', 'pdg_prod3', 'charge_prod3', 'stability_prod3']
    
    parsed_data = parse_file(infile)

    try:
        check_consistency_infile(nvars=len(vars_names), ncols=len(parsed_data[0][2]))
    except ValueError as e:
        print(f"- convertEvtCalc - Error: {e}")
        sys.exit(1)

    if parsed_data:
        root_file = r.TFile(outfile, "RECREATE")
        
        tree = r.TTree("LLP_tree", "LLP_tree")
        
        branch = {}
        for var in vars_names:
            branch[var] = np.zeros(1, dtype=float)
            tree.Branch(var, branch[var], f"{var}/D")

        for pt, sp, vars in parsed_data:
            for row in zip(*vars):
                for i, value in enumerate(row):
                    if i<len(vars_names):  branch[vars_names[i]][0] = value
                tree.Fill()
        
        tree.Write()
        root_file.Close()
        print(f"- convertEvtCalc - ROOT file '{outfile}' created successfully.")
        return outfile
 