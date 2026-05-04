#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Event display for time window straw tracker hits.

Reads time_windows.root (output of make_time_window.py) and produces
scatter plots of straw tube hits colored by sub-event.  Three views
per time window: Z-X, Z-Y, and X-Y.
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
import ROOT
from matplotlib.backends.backend_pdf import PdfPages


def read_window(tree, meta_tree, event_num):
    """Read straw hits and sub-event mapping for one time window.

    Returns arrays (x, y, z, sub_event) or None if no straw hits.
    """
    tree.GetEntry(event_num)
    meta_tree.GetEntry(event_num)

    tracks = tree.MCTrack
    points = tree.strawtubesPoint

    if not len(points):
        return None

    x = np.empty(len(points))
    y = np.empty(len(points))
    z = np.empty(len(points))
    sub_event = np.empty(len(points), dtype=int)

    for i, pt in enumerate(points):
        x[i] = pt.GetX()
        y[i] = pt.GetY()
        z[i] = pt.GetZ()
        tid = pt.GetTrackID()
        if 0 <= tid < len(tracks):
            sub_event[i] = tracks[tid].GetEventID()
        else:
            sub_event[i] = -1

    return x, y, z, sub_event


def plot_window(fig, x, y, z, sub_event, event_num, n_overlaid):
    """Draw three views of straw hits colored by sub-event."""
    fig.clf()
    fig.suptitle(f"Time window {event_num} ({n_overlaid} sub-events, {len(x)} straw hits)")

    unique_events = np.unique(sub_event)
    cmap = plt.cm.tab10 if len(unique_events) <= 10 else plt.cm.tab20
    colors = {ev: cmap(i % cmap.N) for i, ev in enumerate(unique_events)}
    c = [colors[ev] for ev in sub_event]

    ax_zx = fig.add_subplot(2, 2, 1)
    ax_zx.scatter(z, x, c=c, s=2, edgecolors="none")
    ax_zx.set_xlabel("z [cm]")
    ax_zx.set_ylabel("x [cm]")

    ax_zy = fig.add_subplot(2, 2, 2)
    ax_zy.scatter(z, y, c=c, s=2, edgecolors="none")
    ax_zy.set_xlabel("z [cm]")
    ax_zy.set_ylabel("y [cm]")

    ax_xy = fig.add_subplot(2, 2, 3)
    ax_xy.scatter(x, y, c=c, s=2, edgecolors="none")
    ax_xy.set_xlabel("x [cm]")
    ax_xy.set_ylabel("y [cm]")
    ax_xy.set_aspect("equal")

    # Legend in fourth panel
    ax_leg = fig.add_subplot(2, 2, 4)
    ax_leg.axis("off")
    for ev in unique_events:
        n = np.sum(sub_event == ev)
        ax_leg.scatter([], [], c=[colors[ev]], s=20, label=f"sub-event {ev} ({n} hits)")
    ax_leg.legend(loc="center", fontsize="small", ncol=1)

    fig.tight_layout()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", help="Time window ROOT file")
    parser.add_argument("-o", "--output", default=None, help="Output PDF (default: <input>_display.pdf)")
    parser.add_argument("--event", type=int, default=None, help="Display single window interactively")
    args = parser.parse_args()

    f = ROOT.TFile.Open(args.input_file)
    tree = f.Get("cbmsim")
    meta_tree = f.Get("timewindow_meta")
    n_windows = tree.GetEntries()

    if args.event is not None:
        # Single window, interactive
        data = read_window(tree, meta_tree, args.event)
        if data is None:
            print(f"No straw hits in window {args.event}")
            return
        x, y, z, sub_event = data
        meta_tree.GetEntry(args.event)
        fig = plt.figure(figsize=(12, 10))
        plot_window(fig, x, y, z, sub_event, args.event, meta_tree.n_overlaid)
        plt.show()
    else:
        # All windows to PDF
        output = args.output or args.input_file.replace(".root", "_display.pdf")
        fig = plt.figure(figsize=(12, 10))
        with PdfPages(output) as pdf:
            for i in range(n_windows):
                data = read_window(tree, meta_tree, i)
                if data is None:
                    continue
                x, y, z, sub_event = data
                meta_tree.GetEntry(i)
                plot_window(fig, x, y, z, sub_event, i, meta_tree.n_overlaid)
                pdf.savefig(fig)
                if (i + 1) % 10 == 0 or i == n_windows - 1:
                    print(f"\r{i + 1}/{n_windows} windows", end="", flush=True)
            print()
        print(f"Written to {output}")

    f.Close()


if __name__ == "__main__":
    main()
