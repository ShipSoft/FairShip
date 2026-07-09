#!/usr/bin/env python3
import ROOT
import numpy as np
import argparse
from array import array
import math

def safe_div(numer, denom):
    if denom is None:
        return 0.00
    try:
        if denom == 0.00 or math.isinf(denom) or denom > 1e12:
            return 0.00
        return numer / denom
    except Exception:
        return 0.00

def vec2str(v):
    return f"[{v[0]:6.2f} {v[1]:6.2f} {v[2]:6.2f}]"

def propagate_and_measure(start, end, step_len=0.001):
    """
    start, end: in cm
    step_len: step lenght in cm
    """
    start_np = np.array(start, dtype=np.float64)
    end_np   = np.array(end, dtype=np.float64)
    vec = end_np - start_np
    total_length = np.linalg.norm(vec)
    if total_length == 0.00:
        print("Start == End, nothing to do.")
        return
    direction_np = vec / total_length

    nav = ROOT.gGeoManager.GetCurrentNavigator()

    # Initializing start
    pos = start_np.copy()
    point = array('d', pos.tolist())
    direction = array('d', direction_np.tolist())
    nav.InitTrack(point, direction)
    node = nav.GetCurrentNode()
    vol = node.GetVolume()
    mat = vol.GetMaterial()
    current_material = mat.GetName()
    mat_start = pos.copy()

    # Cumulatives
    accum_X0_cont = 0.00
    accum_lambdaI_cont = 0.00
    accum_X0_at_block_start = 0.00
    accum_lambdaI_at_block_start = 0.00
    accumulated = {}

    print("\n== Material scan ==")
    print(f"From {start_np} to {end_np}")
    print(f"Total distance = {total_length:.2f} cm\n")
    print(" Len(cm)   X0(units)  λI(units)   Material        Entry[x,y,z]       Exit[x,y,z]")
    print("-"*85)

    traveled = 0.00
    # Iteration inside material
    while traveled < total_length:
        this_step = min(step_len, total_length - traveled)
        pos += direction_np * this_step
        traveled += this_step
        point = array('d', pos.tolist())
        nav.InitTrack(point, direction)
        node = nav.GetCurrentNode()
        vol = node.GetVolume()
        mat = vol.GetMaterial()
        mat_name = mat.GetName()
        X0_cm = mat.GetRadLen()
        lambdaI_cm = mat.GetIntLen()

        # To avoid X0=0 errros
        if X0_cm and not math.isinf(X0_cm):
            accum_X0_cont += this_step / X0_cm
        if lambdaI_cm and not math.isinf(lambdaI_cm):
            accum_lambdaI_cont += this_step / lambdaI_cm

        # Closing material
        if mat_name != current_material or traveled >= total_length:
            length_mat = np.linalg.norm(pos - mat_start)
            block_X0_units = accum_X0_cont - accum_X0_at_block_start
            block_lambda_units = accum_lambdaI_cont - accum_lambdaI_at_block_start

            print(f"{length_mat:8.2f}   {block_X0_units:9.2f}   {block_lambda_units:9.2f}   "
                  f"{current_material:12}   {vec2str(mat_start)}   {vec2str(pos)}")
            accumulated[current_material] = accumulated.get(current_material, 0.00) + length_mat

            # Preparing next block
            current_material = mat_name
            mat_start = pos.copy()
            accum_X0_at_block_start = accum_X0_cont
            accum_lambdaI_at_block_start = accum_lambdaI_cont

    if np.linalg.norm(pos - mat_start) > 1e-9:
        length_mat = np.linalg.norm(pos - mat_start)

        nav.InitTrack(array('d', pos.tolist()), direction)
        node = nav.GetCurrentNode()
        vol = node.GetVolume()
        mat = vol.GetMaterial()
        X0_mm = mat.GetRadLen()
        lambdaI_mm = mat.GetIntLen()

        block_X0_units = accum_X0_cont - accum_X0_at_block_start
        block_lambda_units = accum_lambdaI_cont - accum_lambdaI_at_block_start

        print(f"{length_mat:8.1f}   {block_X0_units:9.3f}   {block_lambda_units:10.3f}   "
              f"{current_material:12}   {vec2str(mat_start)}   {vec2str(pos)}")

        accumulated[current_material] = accumulated.get(current_material, 0.00) + length_mat

    # Totals
    print("\n== Totals per material ==")
    print("Material       TotalLen(cm)")
    for mat_name, length in accumulated.items():
        print(f"{mat_name:12} {length:12.1f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, help="Geometry ROOT file")
    parser.add_argument("--start", type=float, nargs=3, required=True, help="Start x y z (cm)")
    parser.add_argument("--end",   type=float, nargs=3, required=True, help="End x y z (cm)")
    parser.add_argument("--step",  type=float, default=0.001, help="Step size in cm (default: 0.001 cm)")
    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)
    ROOT.TGeoManager.Import(args.file)
    ROOT.gGeoManager.CloseGeometry()
    propagate_and_measure(args.start, args.end, args.step)

if __name__ == "__main__":
    main()
