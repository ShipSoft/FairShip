# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import math
from dataclasses import dataclass, field
from typing import Any

import global_variables
import ROOT
from BaseDetector import BaseDetector


@dataclass
class _FiredTile:
    """MC points collected in one constituent tile."""

    first: Any  # earliest UpstreamTaggerPoint in the tile
    position: ROOT.TVector3  # tile center
    points: list[int] = field(default_factory=list)  # indices of its MC points
    signals: list[float] = field(default_factory=list)  # unrounded ADC signal of each point


class UpstreamTaggerDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None, mcBranchName=None) -> None:
        super().__init__(name, intree, mcBranchName=mcBranchName, outtree=outtree)
        # Parallel to the MC link: for each hit, the unrounded ADC signal of
        # each of its MC points, in the same order as the point indices.
        self.MCadc = None
        if mcBranchName:
            self.MCadc = ROOT.std.vector("std::vector<float>")()
            self.outtree.Branch(f"{mcBranchName}ADC", self.MCadc)

        # The UBT parameters are the same for every MC point of the run: read
        # them once here.
        ubt_geo = global_variables.ShipGeo.UpstreamTagger
        # Region ID -> constituent tile side. Some ROOT/Python serialization
        # paths stringify the dictionary keys.
        self._tile_sizes = {int(region): float(size) for region, size in ubt_geo.RegionTileSize.items()}
        self._grid_x = (ubt_geo.TileGridOriginX, ubt_geo.TileGridEndX)
        self._grid_y = (ubt_geo.TileGridOriginY, ubt_geo.TileGridEndY)
        self._z = ubt_geo.z
        self._time_res = ubt_geo.TimeResolution
        self._trigger_threshold = ubt_geo.ADCTriggerThreshold

        # Tile-ID grid: cells of the smallest tile side over the tile grid, and
        # for each tile side the offset of its ID namespace (see tile_id).
        self._grid_size = min(self._tile_sizes.values())
        if self._grid_size <= 0.0:
            raise ValueError(f"Invalid UBT tile-ID grid size: {self._grid_size}")
        self._columns = round((self._grid_x[1] - self._grid_x[0]) / self._grid_size)
        self._rows = round((self._grid_y[1] - self._grid_y[0]) / self._grid_size)
        self._id_offsets = {}
        for tile_size in set(self._tile_sizes.values()):
            multiple = round(tile_size / self._grid_size)
            if multiple <= 0 or not math.isclose(tile_size, multiple * self._grid_size, rel_tol=0.0, abs_tol=1.0e-9):
                raise ValueError(
                    f"UBT tile size {tile_size} cm is not an integer multiple of the tile-ID base cell size"
                    f" {self._grid_size} cm"
                )
            self._id_offsets[tile_size] = (multiple - 1) * self._columns * self._rows

        self._adc_response_maps = self._load_adc_response_maps(
            ubt_geo.ADCResponseMapFile, set(self._tile_sizes.values())
        )

    def delete(self) -> None:
        """Clear the hit, MC link and per-point ADC containers."""
        super().delete()
        if self.MCadc is not None:
            self.MCadc.clear()

    @staticmethod
    def _load_adc_response_maps(path: str, tile_sizes: set[float]) -> dict[float, ROOT.TH2D]:
        """Load the ADC/MeV vs local position (mm) TH2D for each tile size (cm)."""
        # PyROOT raises OSError when the file cannot be opened, also when it is
        # not a ROOT file, e.g. a Git LFS pointer that was not fetched.
        try:
            response_file = ROOT.TFile.Open(path)
        except OSError as error:
            raise OSError(
                f"Cannot open the UBT ADC response map file {path}; it is stored with Git LFS, so run `git lfs pull`"
                " if it has not been fetched"
            ) from error
        maps = {}
        for tile_size in tile_sizes:
            name = f"adc_per_mev_{round(10.0 * tile_size)}mm"
            histogram = response_file.Get(name)
            if not isinstance(histogram, ROOT.TH2D):
                raise ValueError(f"UBT ADC response map {path} has no TH2D '{name}'")
            histogram.SetDirectory(ROOT.gROOT)
            maps[tile_size] = histogram
        response_file.Close()
        return maps

    def get_constituent_tile_size(self, detector_id: int) -> float:
        """Return the side length for the tiles represented by a region hit."""
        return self._tile_sizes[detector_id]

    @staticmethod
    def _tile_center(coordinate: float, grid_origin: float, grid_end: float, tile_size: float) -> float:
        """Return the globally aligned tile center containing coordinate."""
        coordinate = min(max(coordinate, grid_origin), math.nextafter(grid_end, grid_origin))
        tile_count = round((grid_end - grid_origin) / tile_size)
        if tile_count <= 0:
            raise ValueError(f"Invalid UBT tile grid [{grid_origin}, {grid_end}] with tile size {tile_size}")
        # At the positive boundary, floating-point subtraction and division
        # can round nextafter(grid_end, grid_origin) back to an exact quotient
        # of tile_count. Cap the result so the last valid tile is selected.
        tile_index = min(math.floor((coordinate - grid_origin) / tile_size), tile_count - 1)
        return grid_origin + (tile_index + 0.5) * tile_size

    def digitized_position(self, point, tile_size: float) -> ROOT.TVector3:
        """Map an MC point to the center of its 2x2 or 4x4 cm2 tile."""
        x = self._tile_center(point.GetX(), self._grid_x[0], self._grid_x[1], tile_size)
        y = self._tile_center(point.GetY(), self._grid_y[0], self._grid_y[1], tile_size)
        return ROOT.TVector3(x, y, self._z)

    def tile_id(self, position: ROOT.TVector3, tile_size: float) -> int:
        """Return a stable unique ID for a constituent tile.

        The tile is identified by its lower-left cell on the tile-ID grid, the
        grid of the smallest tile side (2 cm) over the tile grid bounds, with
        ``columns`` x ``rows`` cells:

            tile ID = (tile side / grid size - 1) * columns * rows + row * columns + column

        So each tile side has its own range of ``columns * rows`` IDs, and a
        2 cm and a 4 cm tile with the same lower-left cell get different IDs.
        For the default geometry (340 x 504 cm2, 170 x 252 cells), the range
        of 2 cm tiles is [0, 42840) and that of 4 cm tiles [42840, 85680). The
        stride follows the UBT box, so decoding an ID needs the grid of its
        geometry:

            side_index, cell = divmod(tile_id, columns * rows)
            row, column = divmod(cell, columns)
        """
        column = round((position.X() - tile_size / 2.0 - self._grid_x[0]) / self._grid_size)
        row = round((position.Y() - tile_size / 2.0 - self._grid_y[0]) / self._grid_size)
        if not (0 <= column < self._columns and 0 <= row < self._rows):
            raise ValueError(
                f"UBT tile at ({position.X()}, {position.Y()}) cm with size {tile_size} cm "
                f"maps to cell ({column}, {row}), outside the {self._columns} x {self._rows} tile-ID grid; "
                f"x bounds={self._grid_x} cm, y bounds={self._grid_y} cm, base cell size={self._grid_size} cm"
            )
        return self._id_offsets[tile_size] + row * self._columns + column

    def adc_signal(self, point, tile_center: ROOT.TVector3, tile_size: float) -> float:
        """Return the (unrounded) ADC signal of a point from its energy and position in the tile."""
        # FairShip positions are in cm and the response-map coordinates are mm.
        local_x_mm = 10.0 * (point.GetX() - tile_center.X())
        local_y_mm = 10.0 * (point.GetY() - tile_center.Y())
        response_map = self._adc_response_maps[tile_size]
        # Clamp to the outermost bins so hits on a tile edge do not land in
        # the under/overflow bins.
        x_axis = response_map.GetXaxis()
        y_axis = response_map.GetYaxis()
        x_bin = min(max(x_axis.FindFixBin(local_x_mm), 1), x_axis.GetNbins())
        y_bin = min(max(y_axis.FindFixBin(local_y_mm), 1), y_axis.GetNbins())
        adc_per_mev = response_map.GetBinContent(x_bin, y_bin)
        deposited_energy_mev = 1000.0 * point.GetEnergyLoss()
        return deposited_energy_mev * adc_per_mev

    def digitize(self) -> None:
        """Digitize UBT MC points into one hit per fired constituent tile.

        An MC point covers a (track, region) pair and a region holds 25 or 100
        tiles, so a tile can collect points of several tracks, e.g. a muon and
        a delta ray. Their ADC signals, each taken at its own position in the
        tile, are summed before rounding and before the trigger threshold is
        applied. The hit time is that of the first point in the tile.
        """
        tiles: dict[int, _FiredTile] = {}  # by tile ID, in the order of their first point
        for index, aMCPoint in enumerate(self.intree.UpstreamTaggerPoint):
            tile_size = self._tile_sizes[aMCPoint.GetDetectorID()]
            position = self.digitized_position(aMCPoint, tile_size)
            tile_id = self.tile_id(position, tile_size)
            tile = tiles.get(tile_id)
            if tile is None:
                tile = tiles[tile_id] = _FiredTile(aMCPoint, position)
            elif aMCPoint.GetTime() < tile.first.GetTime():
                tile.first = aMCPoint
            tile.points.append(index)
            tile.signals.append(self.adc_signal(aMCPoint, position, tile_size))

        for tile_id, tile in tiles.items():
            adc_counts = max(0, round(sum(tile.signals)))
            aHit = ROOT.UpstreamTaggerHit(tile.first, self.intree.t0, tile.position, self._time_res)
            aHit.SetTileID(tile_id)
            aHit.SetADC(adc_counts)
            aHit.SetTriggered(adc_counts >= self._trigger_threshold)
            self.det.push_back(aHit)
            if self.MCdet is not None:
                self.MCdet.push_back(ROOT.std.vector("int")(tile.points))
            if self.MCadc is not None:
                self.MCadc.push_back(ROOT.std.vector("float")(tile.signals))
