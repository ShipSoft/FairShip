"""Mapping between detector modules and SciFi channels."""

import argparse

import matplotlib.patches as patches
import matplotlib.pyplot as plt
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

    def draw_channel(self, channel):
        """Draw a single channel mapping showing fibre positions and the SiPM sensor.

        Parameters
        ----------
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
            loc = self.scifi.GetLocalPos(globfiberID, AF)
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
        loc = self.scifi.GetLocalPos(globfiberID, AF)
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
        output_file="scifi_mapping_all_channels.pdf",
        figsize=(16, 16),
        dpi=300,
        cmap_name="tab20",
        alpha_fibre=0.4,
    ):
        """Draw overlay plot of multiple channel mappings on a single figure.

        Parameters
        ----------
        output_file : str, optional
            Filename for the saved PDF plot. Default: 'scifi_mapping_all_channels.pdf'.
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

        # Select your channels. Hardcoded range for demonstration
        channelsU = sorted(self.fibre_to_simp_map_U.keys())[:10]
        channelsV = sorted(self.fibre_to_simp_map_V.keys())[::-1][86:96]
        channels = channelsU + channelsV
        n_chan = len(channels)

        # Build a colormap for rectangles
        cmap = plt.get_cmap(cmap_name)
        colors = [cmap(i / (n_chan - 1)) for i in range(n_chan)]

        # Geometry constants
        fibreVol = sGeo.FindVolumeFast("FiberVol")
        R = fibreVol.GetShape().GetDX()
        DX, DZ = 0.025, 0.135 / 2

        AF = ROOT.TVector3()
        BF = ROOT.TVector3()

        # Loop through all channels
        for idx, chan in enumerate(channels):
            col = colors[idx]

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
                loc = self.scifi.GetLocalPos(fibreID, AF)
                xs.append(loc[0])
                ys.append(loc[2])

            # draw fibres (still orange)
            for x, y in zip(xs, ys):
                ell = patches.Ellipse(
                    (x, y), 2 * R, 2 * R, color="orange", alpha=alpha_fibre
                )
                ax.add_patch(ell)

            # draw SiPM rect in its unique shade
            self.scifi.GetSiPMPosition(chan, BF, AF)
            loc_siPM = self.scifi.GetLocalPos(fibreID, AF)
            rx, ry = loc_siPM[0], loc_siPM[2]
            rect = patches.Rectangle(
                (rx - DX, ry - DZ),
                2 * DX,
                2 * DZ,
                linewidth=1,
                edgecolor="black",
                facecolor=col,
                alpha=alpha_fibre * 0.8,
                hatch="//",
            )
            ax.add_patch(rect)

            # compute a fontsize that fits the rect width
            # 1) data→display coords:
            p0 = ax.transData.transform((rx - DX, ry))
            p1 = ax.transData.transform((rx + DX, ry))
            disp_width = abs(p1[0] - p0[0])
            # 2) convert px→points (1pt = 1/72in; fig.dpi px/inch):
            pts = disp_width * 72.0 / fig.dpi
            fontsize = max(4, min(12, pts * 0.8))

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SciFiMapping visualization tool")
    parser.add_argument(
        "-g",
        dest="geoFile",
        type=str,
        default="geofile_full.conical.PG_13-TGeant4.root",
        help="Path to the geometry ROOT file",
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
    mapping.draw_channel(channel=101104120)  # Example channel
    mapping.draw_many_channels(output_file="scifi_mapping_all_channels.pdf")
