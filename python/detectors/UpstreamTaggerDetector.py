# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import math

import global_variables
import ROOT
from BaseDetector import BaseDetector


class UpstreamTaggerDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None) -> None:
        super().__init__(name, intree, outtree=outtree)
        ubt_geo = global_variables.ShipGeo.UpstreamTagger
        tile_sizes = {round(float(size), 6) for size in ubt_geo.RegionTileSize.values()}
        self._adc_response_maps = self._load_adc_response_maps(ubt_geo.ADCResponseMapFile, tile_sizes)

    @staticmethod
    def _load_adc_response_maps(path: str, tile_sizes: set[float]) -> dict[float, ROOT.TH2D]:
        """Load the ADC/MeV vs local position (mm) TH2D for each tile size (cm)."""
        response_file = ROOT.TFile.Open(path)
        if not response_file or response_file.IsZombie():
            raise OSError(f"Cannot open UBT ADC response map file: {path}")
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

    @staticmethod
    def get_constituent_tile_size(detector_id: int) -> float:
        """Return the side length for the tiles represented by a region hit."""
        tile_sizes = global_variables.ShipGeo.UpstreamTagger.RegionTileSize
        try:
            return tile_sizes[detector_id]
        except KeyError:
            # Some ROOT/Python serialization paths stringify dictionary keys.
            return tile_sizes[str(detector_id)]

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

    @classmethod
    def digitized_position(cls, point) -> ROOT.TVector3:
        """Map an MC point to the center of its 2x2 or 4x4 cm2 tile."""
        ubt_geo = global_variables.ShipGeo.UpstreamTagger
        tile_size = cls.get_constituent_tile_size(point.GetDetectorID())
        x = cls._tile_center(point.GetX(), ubt_geo.TileGridOriginX, ubt_geo.TileGridEndX, tile_size)
        y = cls._tile_center(point.GetY(), ubt_geo.TileGridOriginY, ubt_geo.TileGridEndY, tile_size)
        return ROOT.TVector3(x, y, ubt_geo.z)

    @staticmethod
    def tile_id(position: ROOT.TVector3, tile_size: float) -> int:
        """Return a stable unique ID for a constituent tile.

        The low part is the row-major index of the tile's lower-left cell on
        the global 2 cm UBT grid. Separate 90000-ID namespaces are used for
        each tile-size multiple, preventing a 2 cm tile and a 4 cm tile with
        the same lower-left grid cell from receiving the same ID.
        """
        ubt_geo = global_variables.ShipGeo.UpstreamTagger
        grid_size = min(float(size) for size in ubt_geo.RegionTileSize.values())
        if grid_size <= 0.0:
            raise ValueError(f"Invalid UBT tile-ID grid size: {grid_size}")
        columns = round((ubt_geo.TileGridEndX - ubt_geo.TileGridOriginX) / grid_size)
        rows = round((ubt_geo.TileGridEndY - ubt_geo.TileGridOriginY) / grid_size)
        column = round((position.X() - tile_size / 2.0 - ubt_geo.TileGridOriginX) / grid_size)
        row = round((position.Y() - tile_size / 2.0 - ubt_geo.TileGridOriginY) / grid_size)
        if not (0 <= column < columns and 0 <= row < rows):
            raise ValueError(
                f"UBT tile at ({position.X()}, {position.Y()}) cm with size {tile_size} cm "
                f"maps to cell ({column}, {row}), outside the {columns} x {rows} tile-ID grid; "
                f"x bounds=({ubt_geo.TileGridOriginX}, {ubt_geo.TileGridEndX}) cm, "
                f"y bounds=({ubt_geo.TileGridOriginY}, {ubt_geo.TileGridEndY}) cm, "
                f"base cell size={grid_size} cm"
            )
        tile_size_multiple = round(tile_size / grid_size)
        if tile_size_multiple <= 0 or not math.isclose(
            tile_size, tile_size_multiple * grid_size, rel_tol=0.0, abs_tol=1.0e-9
        ):
            raise ValueError(
                f"UBT tile size {tile_size} cm is not an integer multiple of the tile-ID base cell size {grid_size} cm"
            )
        cells_per_grid = columns * rows
        size_namespace = tile_size_multiple - 1
        return size_namespace * cells_per_grid + row * columns + column

    def adc_counts(self, point, tile_center: ROOT.TVector3, tile_size: float) -> int:
        """Calculate ADC counts from deposited energy and local hit position."""
        # FairShip positions are in cm and the response-map coordinates are mm.
        local_x_mm = 10.0 * (point.GetX() - tile_center.X())
        local_y_mm = 10.0 * (point.GetY() - tile_center.Y())
        response_map = self._adc_response_maps[round(tile_size, 6)]
        # Clamp to the outermost bins so hits on a tile edge do not land in
        # the under/overflow bins.
        x_axis = response_map.GetXaxis()
        y_axis = response_map.GetYaxis()
        x_bin = min(max(x_axis.FindFixBin(local_x_mm), 1), x_axis.GetNbins())
        y_bin = min(max(y_axis.FindFixBin(local_y_mm), 1), y_axis.GetNbins())
        adc_per_mev = response_map.GetBinContent(x_bin, y_bin)
        deposited_energy_mev = 1000.0 * point.GetEnergyLoss()
        return max(0, round(deposited_energy_mev * adc_per_mev))

    def digitize(self) -> None:
        ship_geo = global_variables.ShipGeo
        time_res = ship_geo.UpstreamTagger.TimeResolution
        trigger_threshold = ship_geo.UpstreamTagger.ADCTriggerThreshold

        for aMCPoint in self.intree.UpstreamTaggerPoint:
            position = self.digitized_position(aMCPoint)
            tile_size = self.get_constituent_tile_size(aMCPoint.GetDetectorID())
            adc_counts = self.adc_counts(aMCPoint, position, tile_size)
            aHit = ROOT.UpstreamTaggerHit(aMCPoint, self.intree.t0, position, time_res)
            aHit.SetTileID(self.tile_id(position, tile_size))
            aHit.SetADC(adc_counts)
            aHit.SetTriggered(adc_counts >= trigger_threshold)
            self.det.push_back(aHit)
