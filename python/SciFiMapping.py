# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration


"""Mapping between detector modules and SciFi channels."""

import argparse

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import ROOT
import shipDet_conf
from ShipGeoConfig import load_from_root_file


class SciFiMapping:
    """Mapping between detector modules and SciFi channels."""

    def __init__(self, modules):
        """Initialize the SciFiMapping instance with geometry modules.

        Parameters
        ----------
        modules : dict
            Dictionary of detector geometry modules, must include key 'MTC'.

        """
        self.modules = modules
        self.scifi = modules["MTC"]

    def create_fibre_to_simp_map(self):
        """Build mappings from optical fibres to SiPM channels for U and V planes.

        Retrieves the U and V SiPM maps from the SciFi module and constructs
        dictionaries mapping each fibre index to its associated SiPM channels,
        including weight and x-position information.

        For full details, see SND/MTC/MTCDetector.cxx in the SND framework.

        Side Effects
        ------------
        Sets attributes 'fibre_to_simp_map_U' and 'fibre_to_simp_map_V'.
        """
        FU, FV = self.scifi.GetSiPMmapU(), self.scifi.GetSiPMmapV()
        self.fibre_to_simp_map_U, self.fibre_to_simp_map_V = {}, {}
        for x1, x2 in zip(FU, FV):
            self.fibre_to_simp_map_U[x1.first] = {}
            for z in x1.second:
                self.fibre_to_simp_map_U[x1.first][z.first] = {
                    "weight": z.second[0],
                    "xpos": z.second[1],
                }
            self.fibre_to_simp_map_V[x2.first] = {}
            for z in x2.second:
                self.fibre_to_simp_map_V[x2.first][z.first] = {
                    "weight": z.second[0],
                    "xpos": z.second[1],
                }

    def create_sipm_to_fibre_map(self):
        """Build mappings from SiPM channels to optical fibres for U and V planes.

        Retrieves the U and V fibre maps from the SciFi module and constructs
        dictionaries mapping each SiPM channel index to its associated fibres,
        including weight and x-position information.

        For full details, see SND/MTC/MTCDetector.cxx in the SND framework.

        Side Effects
        ------------
        Sets attributes 'sipm_to_fibre_map_U' and 'sipm_to_fibre_map_V'.
        """
        XU, XV = self.scifi.GetFibresMapU(), self.scifi.GetFibresMapV()
        self.sipm_to_fibre_map_U, self.sipm_to_fibre_map_V = {}, {}
        for x1, x2 in zip(XU, XV):
            self.sipm_to_fibre_map_U[x1.first] = {}
            for z in x1.second:
                self.sipm_to_fibre_map_U[x1.first][z.first] = {
                    "weight": z.second[0],
                    "xpos": z.second[1],
                }
            self.sipm_to_fibre_map_V[x2.first] = {}
            for z in x2.second:
                self.sipm_to_fibre_map_V[x2.first][z.first] = {
                    "weight": z.second[0],
                    "xpos": z.second[1],
                }

    def create_sipm_to_position_map(self):
        """Create a mapping from SiPM channels to their positions in the SciFi detector.

        This method retrieves the SiPM positions for both U and V planes and constructs
        dictionaries mapping each SiPM channel index to its corresponding position.

        Side Effects
        ------------
        Sets attributes 'sipm_pos_U' and 'sipm_pos_V'.
        """
        sipm_pos_U_raw = self.scifi.GetSiPMPos_U()
        sipm_pos_V_raw = self.scifi.GetSiPMPos_V()
        self.sipm_pos_U, self.sipm_pos_V = {}, {}

        for pair in sipm_pos_U_raw:
            self.sipm_pos_U[pair.first] = pair.second
        for pair in sipm_pos_V_raw:
            self.sipm_pos_V[pair.first] = pair.second

    def make_mapping(self):
        """Execute the full mapping sequence for the SciFi detector.

        Calls internal methods to calculate SiPM overlap, perform the mapping
        in the SciFi module, and build both fibre-to-SiPM and SiPM-to-fibre maps.

        Currently is used in python/shipDigiReco.py.
        """
        self.scifi.SiPMOverlap()
        self.scifi.SiPMmapping()
        self.create_fibre_to_simp_map()
        self.create_sipm_to_fibre_map()
        self.create_sipm_to_position_map()

    def get_sipm_to_fibre_map(self):
        """Retrieve the SiPM-to-fibre mapping dictionaries.

        Returns
        -------
        tuple of dict
            (sipm_to_fibre_map_U, sipm_to_fibre_map_V)

        """
        return self.sipm_to_fibre_map_U, self.sipm_to_fibre_map_V

    def get_fibre_to_simp_map(self):
        """Retrieve the fibre-to-SiPM mapping dictionaries.

        Returns
        -------
        tuple of dict
            (fibre_to_simp_map_U, fibre_to_simp_map_V)

        """
        return self.fibre_to_simp_map_U, self.fibre_to_simp_map_V

    def draw_channel(self, sGeo, channel):
        """Draw a single channel mapping showing fibre positions and the SiPM sensor.

        Parameters
        ----------
        sGeo: ROOT.TGeoManager
            The geometry manager for the detector setup.
        channel : int
            Global channel identifier encoding plane type, SiPM unit, and channel index.

        Side Effects
        ------------
        Saves a PDF file named 'scifi_mapping_channel_1_{channel}.pdf' with the plot.

        """
        AF = ROOT.TVector3()
        BF = ROOT.TVector3()
        plane_type = int(channel / 1e5) % 10
        locChannel = channel % 1000000
        fibreVol = sGeo.FindVolumeFast("FiberVol")
        R = fibreVol.GetShape().GetDX()
        DX = 0.025
        DZ = 0.135
        xmin = 999.0
        xmax = -999.0
        ymin = 999.0
        ymax = -999.0
        fibre_positions = []
        fibresSiPM = (
            self.fibre_to_simp_map_U if plane_type == 0 else self.fibre_to_simp_map_V
        )
        for fibre in fibresSiPM[locChannel]:
            globfiberID = (
                fibre + 100000000 + 1000000 + 0 * 100000
                if plane_type == 0
                else fibre + 100000000 + 1000000 + 1 * 100000
            )
            self.scifi.GetPosition(globfiberID, AF, BF)
            loc = self.scifi.GetLocalPos(globfiberID, BF)
            print(f"Position for fibre {globfiberID} A: {BF.X()}, {BF.Y()}, {BF.Z()}")
            fibre_positions.append((loc[0], loc[2]))
            if xmin > loc[0]:
                xmin = loc[0]
            if ymin > loc[2]:
                ymin = loc[2]
            if xmax < loc[0]:
                xmax = loc[0]
            if ymax < loc[2]:
                ymax = loc[2]
        D = ymax - ymin + 3 * R
        x0 = (xmax + xmin) / 2.0
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(x0 - D / 2, x0 + D / 2)
        ax.set_ylim(ymin - 1.5 * R, ymax + 1.5 * R)
        for i, (x, y) in enumerate(fibre_positions):
            ellipse = patches.Ellipse(
                (x, y), width=2 * R, height=2 * R, color="orange", alpha=0.6
            )
            ax.add_patch(ellipse)
        self.scifi.GetSiPMPosition(locChannel, AF, BF)
        loc = self.scifi.GetLocalPos(globfiberID, BF)
        print(f"SiPM position for channel {channel}: {loc[0]}, {loc[1]}, {loc[2]}")
        rect = patches.Rectangle(
            (loc[0] - DX, loc[2] - DZ),
            2 * DX,
            2 * DZ,
            linewidth=1,
            edgecolor="blue",
            facecolor="blue",
            alpha=0.3,
            hatch="//",
        )
        ax.add_patch(rect)
        ax.set_xlabel("X [cm]")
        ax.set_ylabel("Z [cm]")
        ax.set_title(f"SiPM Mapping for Channel {channel}")
        ax.grid(True)
        ax.set_aspect("equal")
        plt.savefig(f"scifi_mapping_channel_1_{channel}.pdf")

    def draw_many_channels(
        self,
        sGeo,
        number_of_channels=20,
        output_file="scifi_mapping_many_channels.pdf",
        labeling=True,
        figsize=(16, 16),
        dpi=300,
        cmap_name="tab20",
        alpha_fibre=0.4,
    ):
        """Draw overlay plot of multiple channel mappings on a single figure.

        Parameters
        ----------
        number_of_channels : int, optional
            Total number of channels to display (split evenly between U and V planes).
            Default is 20.
        sGeo : ROOT.TGeoManager
            The geometry manager for the detector setup.
        output_file : str, optional
            Filename for the saved PDF plot. Default: 'scifi_mapping_all_channels.pdf'.
        labeling : bool, optional
            If True, annotate each SiPM rectangle with channel information.
            Default is True.
        figsize : tuple of float, optional
            Figure size in inches. Default is (16, 16).
        dpi : int, optional
            Resolution of the figure in dots per inch. Default is 300.
        cmap_name : str, optional
            Matplotlib colormap name for differentiating channels. Default is 'tab20'.
        alpha_fibre : float, optional
            Transparency for fibre ellipses. Default is 0.4.

        Side Effects
        ------------
        Saves an overlay PDF plot with the specified filename.

        """
        # Prepare fig & ax
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Geometry constants
        fibreVol = sGeo.FindVolumeFast("FiberVol")
        R = fibreVol.GetShape().GetDX()
        DX, DZ = 0.025, 0.135 / 2

        # Select your channels. Hardcoded range for demonstration
        # channelsU = sorted(self.fibre_to_simp_map_U.keys())[:10]
        # channelsV = sorted(self.fibre_to_simp_map_V.keys())[::-1][86:96]

        # Find SiPM channel in the center of the U and V planes
        center_channel_U = [
            chan for chan, x_pos in self.sipm_pos_U.items() if abs(x_pos) <= DX - 0.001
        ][0]
        center_channel_V = [
            chan for chan, x_pos in self.sipm_pos_V.items() if abs(x_pos) <= DX - 0.001
        ][0]

        def get_surrounding_keys(d: dict, target_key, N: int):
            """Return neighbors of `target_key` in value-sorted order.

            Given a dict `d`, find `target_key` in the ordering of keys sorted by
            their values, and return up to N//2 keys that come before it and N//2 keys
            that come after it (excluding the target_key itself).

            Parameters
            ----------
            d : dict
                Mapping from keys to comparable values.
            target_key : hashable
                The key around which to collect neighbors.
            N : int
                Total number of neighbors to return (N//2 before, N//2 after).

            Returns
            -------
            list
                List of up to N keys: first the keys before, then the keys after.

            """
            # 1) sort keys by their associated values
            sorted_keys = sorted(d.keys(), key=lambda k: d[k])
            # 2) locate the target
            try:
                idx = sorted_keys.index(target_key)
            except ValueError:
                raise KeyError(f"Target key {target_key!r} not found in dictionary")

            half = N // 2
            # 3) slice out the neighbors
            start = max(0, idx - half)
            end_before = idx
            start_after = idx + 1
            end_after = idx + 1 + half

            before = sorted_keys[start:end_before]
            after = sorted_keys[start_after:end_after]

            return before + [target_key] + after

        channelsU = get_surrounding_keys(
            self.sipm_pos_U, center_channel_U, number_of_channels
        )
        channelsV = get_surrounding_keys(
            self.sipm_pos_V, center_channel_V, number_of_channels
        )

        channels = channelsU + channelsV
        n_chan = len(channels)

        AF = ROOT.TVector3()
        BF = ROOT.TVector3()

        # Loop through all channels
        for chan in channels:
            isU = chan in channelsU
            # decode local channel
            locChan = chan % 1_000_000

            # collect fibre positions
            xs, ys = [], []
            for fibreID in (
                self.fibre_to_simp_map_U
                if chan in channelsU
                else self.fibre_to_simp_map_V
            )[locChan]:
                globfiberID = (
                    fibreID + 100000000 + 1000000 + 0 * 100000
                    if chan in channelsU
                    else fibreID + 100000000 + 1000000 + 1 * 100000
                )
                self.scifi.GetPosition(globfiberID, AF, BF)
                loc = self.scifi.GetLocalPos(fibreID, BF)
                xs.append(loc[0])
                ys.append(loc[2])

            # draw fibres (still orange)
            for x, y in zip(xs, ys):
                ell = patches.Ellipse(
                    (x, y),
                    2 * R,
                    2 * R,
                    fill=False,
                    edgecolor="black",
                    linewidth=1,
                    alpha=alpha_fibre,
                )
                ax.add_patch(ell)

            # draw SiPM rect in its unique shade
            self.scifi.GetSiPMPosition(chan, BF, AF)
            loc_siPM = self.scifi.GetLocalPos(fibreID, BF)
            rx, ry = loc_siPM[0], loc_siPM[2]
            rect = patches.Rectangle(
                (rx - DX, ry - DZ),
                2 * DX,
                2 * DZ,
                linewidth=1,
                edgecolor="black",
                facecolor="blue"
                if isU
                else "red",  # override with solid colors for clarity,
                alpha=alpha_fibre * 0.8,
                hatch="//" if isU else "\\\\",
            )
            ax.add_patch(rect)

            if labeling:
                # compute a fontsize that fits the rect width
                # 1) data→display coords:
                p0 = ax.transData.transform((rx - DX, ry))
                p1 = ax.transData.transform((rx + DX, ry))
                disp_width = abs(p1[0] - p0[0])
                # 2) convert px→points (1pt = 1/72in; fig.dpi px/inch):
                pts = disp_width * 72.0 / fig.dpi
                fontsize = max(2, min(12, pts * 0.8))

                # label above the rect
                text = f"SiPM: {(chan // 1000) % 10} \n ch: {chan % 1000}"
                ax.text(
                    rx - DX / 2,
                    ry + DZ + R * 0.1,
                    text,
                    ha="left",
                    va="bottom",
                    fontsize=fontsize,
                    color="black",
                    clip_on=True,
                )

        # finalize plot
        ax.relim()
        ax.autoscale_view()
        ax.set_aspect("equal")
        ax.tick_params(axis="both", which="major", labelsize=18)
        ax.tick_params(axis="both", which="minor", labelsize=18)
        ax.set_xlabel("X [cm]", fontsize=20)
        ax.set_ylabel("Z [cm]", fontsize=20)
        ax.set_title("SiPM-Channel Mappings Overlaid", fontsize=24)
        ax.grid(True)

        plt.tight_layout()
        plt.savefig(output_file)
        plt.close(fig)
        print(f"Saved overlay plot of {n_chan} channels to {output_file}")

    def draw_channel_XY(
        self,
        number_of_channels=20,
        real_event=False,
        x_coords=None,
        output_file="scifi_channel_ribbons_XY.pdf",
        figsize=(16, 16),
        dpi=300,
    ):
        """Plot SciFi channel ribbons and SiPM boxes in X–Y view.

        Simplified X–Y view: one ribbon per channel (no per-fiber loops).
        Ribbons span Y from -25 to +25 (length=50 cm), thickness equal
        to channel height = 2*DZ, tilted +5° for U-plane channels, -5° for
        V-plane. SiPM boxes sit on top at y=25→25+2*DZ.

        Parameters
        ----------
        number_of_channels : int
            Total ribbons (split around center) per plane.
        real_event : bool
            If True, highlight ribbons corresponding to given x_coords.
        x_coords : list of float
            If real_event is True, list of two x-coordinates [x_U, x_V] to highlight.
        output_file : str
            Path to save the PDF.
        figsize : tuple of float
            Figure size in inches.
        dpi : int
            Figure resolution in dots per inch.
        Side Effects
        ------------
        Saves a PDF file with the specified filename containing the plot.

        """
        # 2) Geometry constants
        DZ = 0.135 / 2  # SiPM half-height [cm]
        DX = 0.025  # SiPM half-width [cm]
        L = 50.0  # ribbon length (full Y-span) [cm]
        angle_U = -5.0  # tilt for U
        angle_V = +5.0  # tilt for V

        if not real_event:
            alpha_sipm, alpha_fibre = 0.75, 0.5
        else:
            alpha_sipm, alpha_fibre = 0.1, 0.1
            # find the channels corresponding to x_coords
            channels_x_U = next(
                c for c, x in self.sipm_pos_U.items() if abs(x - x_coords[0]) < DX
            )
            channel_x_U = [
                c for c, x in self.sipm_pos_U.items() if abs(x - x_coords[0]) < DX
            ][0]
            channels_x_V = next(
                c for c, x in self.sipm_pos_V.items() if abs(x - x_coords[1]) < DX
            )
            channel_x_V = [
                c for c, x in self.sipm_pos_V.items() if abs(x - x_coords[1]) < DX
            ][0]
        # 1) Figure setup
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # get center channels + neighbors
        centerU = next(c for c, x in self.sipm_pos_U.items() if abs(x) < DX)
        centerV = next(c for c, x in self.sipm_pos_V.items() if abs(x) < DX)

        def get_surrounding(d, target, N):
            keys = sorted(d.keys(), key=lambda k: d[k])
            i = keys.index(target)
            half = N // 2
            start = max(0, i - half)
            end = min(len(keys), i + half + 1)
            return keys[start:end]

        if not real_event:
            chansU = get_surrounding(self.sipm_pos_U, centerU, number_of_channels)
            chansV = get_surrounding(self.sipm_pos_V, centerV, number_of_channels)
        else:
            chansU = get_surrounding(self.sipm_pos_U, channels_x_U, number_of_channels)
            chansV = get_surrounding(self.sipm_pos_V, channels_x_V, number_of_channels)
        all_chans = chansU + chansV

        # cmap_U = plt.get_cmap('tab20')
        # cmap_V = plt.get_cmap('tab20b')
        # colorsU = [cmap_U(i/(len(chansU)-1)) for i in range(len(chansU))]
        # colorsV = [cmap_V(i/(len(chansV)-1)) for i in range(len(chansV))]
        # 3) Draw ribbons and SiPM boxes per channel
        for chan in all_chans:
            isU = chan in chansU
            x0 = self.sipm_pos_U[chan] if isU else self.sipm_pos_V[chan]
            angle = angle_U if isU else angle_V

            alpha = np.deg2rad(angle)  # e.g. angle_deg = +5 or -5
            dx = DX
            dy = L / 2
            shift = dy * np.tan(alpha)  # horizontal shear of bottom edge
            # define the four corners in XY
            coords = [
                (x0 - dx, +dy),  # top-left
                (x0 + dx, +dy),  # top-right
                (x0 + dx - shift, -dy),  # bottom-right
                (x0 - dx - shift, -dy),  # bottom-left
            ]

            # col = colorsU[k_U] if isU else colorsV[k_V]
            col = "blue" if isU else "red"  # override with solid colors for clarity
            if not real_event:
                ribbon = patches.Polygon(
                    coords,
                    closed=True,
                    facecolor=col,  # fill in your color
                    edgecolor="black",
                    alpha=alpha_fibre,  # semi-transparent
                )
                ax.add_patch(ribbon)

                y_top = L / 2 if isU else L / 2 + DZ

                box = patches.Rectangle(
                    (x0 - DX, y_top),
                    2 * DX,
                    DZ,
                    facecolor=col,  # same fill color
                    edgecolor="black",
                    alpha=alpha_sipm,  # a bit more opaque
                    hatch="//" if isU else "\\\\",
                )
                ax.add_patch(box)
            else:
                if channel_x_U == chan or channel_x_V == chan:
                    # draw the ribbon
                    ribbon = patches.Polygon(
                        coords,
                        closed=True,
                        facecolor=col,  # fill in your color
                        edgecolor="black",
                        alpha=0.50,  # semi-transparent
                    )
                    ax.add_patch(ribbon)

                    y_top = L / 2 if isU else L / 2 + DZ

                    box = patches.Rectangle(
                        (x0 - DX, y_top),
                        2 * DX,
                        DZ,
                        facecolor=col,  # same fill color
                        edgecolor="black",
                        alpha=0.75,  # a bit more opaque
                        hatch="//" if isU else "\\\\",
                    )
                    ax.add_patch(box)
                else:
                    ribbon = patches.Polygon(
                        coords,
                        closed=True,
                        facecolor=col,  # fill in your color
                        edgecolor="black",
                        alpha=alpha_fibre,  # semi-transparent
                    )
                    ax.add_patch(ribbon)

                    y_top = L / 2 if isU else L / 2 + DZ

                    box = patches.Rectangle(
                        (x0 - DX, y_top),
                        2 * DX,
                        DZ,
                        facecolor=col,  # same fill color
                        edgecolor="black",
                        alpha=alpha_sipm,  # a bit more opaque
                        hatch="//" if isU else "\\\\",
                    )
                    ax.add_patch(box)

        # 4) Finalize plot
        ax.set_aspect("equal")
        if not real_event:
            shift = 3 * np.tan(alpha)
            min_x = min([self.sipm_pos_U[chan] for chan in chansU]) - shift
            max_x = max(self.sipm_pos_V[chan] for chan in chansV) + shift
            ax.set_xlim(min_x, max_x)
            ax.set_ylim(22, 26)
        else:
            min_x, max_x = -25, 25
            ax.set_ylim(-25, 26)
        ax.set_xlim(min_x, max_x)
        # ax.set_ylim(22, 26)
        ax.set_xlabel("X [cm]")
        ax.set_ylabel("Y [cm]")
        ax.set_title("SciFi channel ribbons & SiPM boxes (X–Y view)")
        ax.grid(True)
        # create legend handles
        legend_handles = [
            patches.Patch(
                facecolor="blue",
                edgecolor="black",
                hatch="//",
                label="U plane",
                alpha=0.75,
            ),
            patches.Patch(
                facecolor="red",
                edgecolor="black",
                hatch="\\\\",
                label="V plane",
                alpha=0.75,
            ),
        ]

        ax.legend(handles=legend_handles, title="Plane", loc="upper right")
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close(fig)
        print(f"Saved channel ribbons + SiPM boxes to {output_file}")

    def draw_combined_scifi_views(
        self,
        sGeo,
        number_of_channels=20,
        output_file="scifi_combined_views.pdf",
        figsize=(18, 8),
        dpi=300,
        alpha_fibre=0.4,
    ):
        """Draw combined Z–X and X–Y views of SciFi channel mappings side by side.

        Parameters
        ----------
        sGeo : ROOT.TGeoManager
            The geometry manager for the detector setup.
        number_of_channels : int, optional
            Total number of channels to display (split evenly between U and V planes).
            Default is 20.
        output_file : str, optional
            Filename for the saved PDF plot. Default: 'scifi_combined_views.pdf'.
        figsize : tuple of float, optional
            Figure size in inches. Default is (18, 8).
        dpi : int, optional
            Resolution of the figure in dots per inch. Default is 300.
        alpha_fibre : float, optional
            Transparency for fibre ellipses. Default is 0.4.
        Side Effects
        ------------
        Saves a PDF file with the specified filename containing the combined views.

        """
        # Prepare fig & axes

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, dpi=dpi)

        fibreVol = sGeo.FindVolumeFast("FiberVol")
        R = fibreVol.GetShape().GetDX()
        DX, DZ = 0.025, 0.135 / 2

        center_U = [
            chan for chan, x in self.sipm_pos_U.items() if abs(x) <= DX - 0.001
        ][0]
        center_V = [
            chan for chan, x in self.sipm_pos_V.items() if abs(x) <= DX - 0.001
        ][0]

        def get_keys(d, target, N):
            ks = sorted(d, key=lambda k: d[k])
            i = ks.index(target)
            half = N // 2
            start = max(0, i - half)
            end = min(len(ks), i + half + 1)
            return ks[start:end]

        chansU = get_keys(self.sipm_pos_U, center_U, number_of_channels)
        chansV = get_keys(self.sipm_pos_V, center_V, number_of_channels)
        channels = chansU + chansV
        n_chan = len(channels)
        cmap = plt.get_cmap("tab20")
        colors = [cmap(i / (n_chan - 1)) for i in range(n_chan)]

        AF = ROOT.TVector3()
        BF = ROOT.TVector3()
        for idx, chan in enumerate(channels):
            col = colors[idx]
            locChan = chan % 1000000
            fmap = (
                self.fibre_to_simp_map_U if chan in chansU else self.fibre_to_simp_map_V
            )
            xs, zs = [], []
            for fid in fmap[locChan]:
                gid = fid + int(1e8 + 1e6 + (0 if chan in chansU else 1) * 1e5)
                self.scifi.GetPosition(gid, AF, BF)
                loc = self.scifi.GetLocalPos(fid, BF)
                xs.append(loc[0])
                zs.append(loc[2])
            for x, z in zip(xs, zs):
                ell = patches.Ellipse(
                    (x, z), 2 * R, 2 * R, color="orange", alpha=alpha_fibre
                )
                ax1.add_patch(ell)
            self.scifi.GetSiPMPosition(chan, BF, AF)
            loc = self.scifi.GetLocalPos(fid, BF)
            rx, rz = loc[0], loc[2]
            rect = patches.Rectangle(
                (rx - DX, rz - DZ),
                2 * DX,
                2 * DZ,
                linewidth=1,
                edgecolor="black",
                facecolor=col,
                alpha=alpha_fibre * 0.8,
            )
            ax1.add_patch(rect)

        ax1.set_xlabel("X [cm]")
        ax1.set_ylabel("Z [cm]")
        ax1.set_aspect("equal")
        ax1.grid(True)
        ax1.set_title("Z–X: SciFi mappings")

        DZ = 0.135 / 2
        DX = 0.025
        L = 50.0
        angleU = 5.0
        angleV = -5.0
        centerU = [c for c, x in self.sipm_pos_U.items() if abs(x) < DX][0]
        centerV = [c for c, x in self.sipm_pos_V.items() if abs(x) < DX][0]
        chansU = get_keys(self.sipm_pos_U, centerU, number_of_channels)
        chansV = get_keys(self.sipm_pos_V, centerV, number_of_channels)
        all_ch = chansU + chansV
        colorsU = [
            plt.get_cmap("Blues")(i / max(len(chansU) - 1, 1))
            for i in range(len(chansU))
        ]
        colorsV = [
            plt.get_cmap("Reds")(i / max(len(chansV) - 1, 1))
            for i in range(len(chansV))
        ]

        for chan in all_ch:
            isU = chan in chansU
            x0 = self.sipm_pos_U[chan] if isU else self.sipm_pos_V[chan]
            angle = angleU if isU else angleV
            alpha_rad = np.deg2rad(angle)
            dy = L / 2
            dx = DX
            shift = dy * np.tan(alpha_rad)
            coords = [
                (x0 - dx, dy),
                (x0 + dx, dy),
                (x0 + dx - shift, -dy),
                (x0 - dx - shift, -dy),
            ]
            col = colorsU[chansU.index(chan)] if isU else colorsV[chansV.index(chan)]
            poly = patches.Polygon(
                coords, closed=True, facecolor=col, edgecolor="black", alpha=0.5
            )
            ax2.add_patch(poly)
            y_top = dy
            box = patches.Rectangle(
                (x0 - DX, y_top),
                2 * DX,
                2 * DZ,
                facecolor=col,
                edgecolor="black",
                alpha=0.75,
            )
            ax2.add_patch(box)

        ax2.set_xlabel("X [cm]")
        ax2.set_ylabel("Y [cm]")
        ax2.set_aspect("equal")
        ax2.grid(True)
        ax2.set_title("X–Y: Channel ribbons")

        legend_handles = [
            patches.Patch(
                facecolor="blue",
                edgecolor="black",
                hatch="//",
                label="U plane",
                alpha=0.75,
            ),
            patches.Patch(
                facecolor="red",
                edgecolor="black",
                hatch="\\",
                label="V plane",
                alpha=0.75,
            ),
        ]
        ax2.legend(handles=legend_handles, title="Plane", loc="upper right")

        plt.tight_layout()
        plt.savefig(output_file)
        plt.close(fig)

    def mapping_validation(self):
        """Validate and print the SiPM-to-fibre and fibre-to-SiPM mappings.

        Prints out the mappings for the U plane, showing fibre indices,
        SiPM channels, weights, and x-positions for both mapping directions.

        """
        sipm_to_fiber_map_U, _ = self.get_sipm_to_fibre_map()
        fiber_to_sipm_map_U, _ = self.get_fibre_to_simp_map()

        print("Validating U plane mapping:")
        for fiber_id, fibers in sipm_to_fiber_map_U.items():
            for sipm_chan, chan_info in fibers.items():
                weight = chan_info["weight"]
                xpos = chan_info["xpos"]
                print(
                    f"""---- Fiber index: {fiber_id}, SiPM Channel: {sipm_chan},
                    Weight: {weight}, X Position: {xpos}"""
                )
        for sipm_chan, sipm_fibers in fiber_to_sipm_map_U.items():
            for fiber_id, fiber_info in sipm_fibers.items():
                weight = fiber_info["weight"]
                xpos = fiber_info["xpos"]
                print(
                    f"""++++ SiPM Channel: {sipm_chan}, Fiber index: {fiber_id},
                    Weight: {weight}, X Position: {xpos}"""
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SciFiMapping visualization tool")
    parser.add_argument(
        "-g",
        dest="geoFile",
        type=str,
        default="geofile_full.conical.PG_13-TGeant4.root",
        help="Path to the geometry ROOT file",
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        type=str,
        default="draw_many_channels",
        help="Operation mode",
        choices=[
            "draw_channel",
            "draw_many_channels",
            "draw_channel_XY",
            "draw_combined_scifi_views",
            "validation",
        ],
    )
    args = parser.parse_args()
    geoFile = args.geoFile
    fgeo = ROOT.TFile.Open(geoFile)
    ship_geo = load_from_root_file(fgeo, "ShipGeo")

    # -----Create geometry----------------------------------------------

    run = ROOT.FairRunSim()
    run.SetName("TGeant4")  # Transport engine
    run.SetSink(
        ROOT.FairRootFileSink(ROOT.TMemFile("output", "recreate"))
    )  # Output file
    run.SetUserConfig("g4Config_basic.C")  # geant4 transport not used
    rtdb = run.GetRuntimeDb()
    modules = shipDet_conf.configure(run, ship_geo)
    run.Init()
    print("configured geofile")
    sGeo = fgeo.FAIRGeom
    top = sGeo.GetTopVolume()
    # -----Create SciFiMapping instance--------------------------------
    mapping = SciFiMapping(modules)
    mapping.make_mapping()

    if args.mode == "draw_channel":
        test_channel = 1000000  # Example channel
        mapping.draw_channel(sGeo, test_channel)
    elif args.mode == "draw_many_channels":
        mapping.draw_many_channels(sGeo, number_of_channels=20)
    elif args.mode == "draw_channel_XY":
        mapping.draw_channel_XY(number_of_channels=20, real_event=False)
    elif args.mode == "draw_combined_scifi_views":
        mapping.draw_combined_scifi_views(sGeo, number_of_channels=20)
    elif args.mode == "validation":
        mapping.mapping_validation()
    else:
        print(f"Unknown mode: {args.mode}")
