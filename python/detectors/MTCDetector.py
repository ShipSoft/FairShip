import ROOT
import global_variables
from BaseDetector import BaseDetector

class MTCDetector(BaseDetector):
    def __init__(self, name, intree, branchType = 'TClonesArray', branchName = None):
        super().__init__(name, intree, branchType, branchName, splitLevel=1)

    def digitize(self):
        """Digitize SND/MTC MC hits.

        Example of fiberID: 123051820, where:
          - 1: MTC unique ID
          - 23: layer number
          - 0: station type (0 for +5 degrees, 1 for -5 degrees, 2 for scint plane)
          - 5: z-layer number (0-5)
          - 1820: local fibre ID within the station
        Example of SiPM global channel (what is seen in the output file): 123004123, where:
          - 1: MTC unique ID
          - 23: layer number
          - 0: station type (0 for +5 degrees, 1 for -5 degrees)
          - 0: mat number (only 0 by June 2025)
          - 4: SiPM number (0-N, where N is the number of SiPMs in the station)
          - 123: number of the SiPM channel (0-127, 128 channels per SiPM)
        """
        hit_container = {}
        mc_points = {}
        norm = {}
        for k, mc_point in enumerate(self.intree.MTCDetPoint):
            det_id = mc_point.GetDetectorID()
            station_type = mc_point.GetStationType() # 0 for +5 degrees, 1 for -5 degrees, 2 for scint plane, extraction: int(fDetectorID / 100000) % 10
            energy_loss = mc_point.GetEnergyLoss()

            if station_type == 0:
                # +5 degrees fiber station uses U fibers
                fibre_map = self.sipm_to_fibre_map_U
            elif station_type == 1:
                # -5 degrees fiber station uses V fibers
                fibre_map = self.sipm_to_fibre_map_V
            elif station_type == 2:
                # Scint Plane. Preserve the same logic as for fibre stations,
                # but use the det_id directly as the global channel.
                global_channel = det_id
                if global_channel not in hit_container:
                    hit_container[global_channel] = []
                    mc_points[global_channel] = {}
                    norm[global_channel] = 0

                weight = 1
                # Append (energy_loss, weight) instead of (mc_point, weight)
                hit_container[global_channel].append([mc_point, weight])
                d_e = energy_loss * weight
                mc_points[global_channel][k] = d_e
                norm[global_channel] += d_e
                continue
            else:
                # Skip any other station_type values
                continue
            # For station_type 0 or 1, look up the local fibre ID
            loc_fibre_id = det_id % 1_000_000
            if loc_fibre_id not in fibre_map:
                # If there is no entry for this fibre ID, skip
                print(f"MTC digitization: no mapping found for fibre ID {loc_fibre_id} in station type {station_type}. Skipping.")
                continue

            for sipm_chan, chan_info in fibre_map[loc_fibre_id].items():
                global_channel = (det_id // 1_000_000) * 1_000_000 + sipm_chan
                if global_channel not in hit_container:
                    hit_container[global_channel] = []
                    mc_points[global_channel] = {}
                    norm[global_channel] = 0

                weight = chan_info['weight']
                hit_container[global_channel].append([mc_point, weight])
                d_e = energy_loss * weight
                mc_points[global_channel][k] = d_e
                norm[global_channel] += d_e

        for det_id in hit_container:
            all_points = ROOT.std.vector('MTCDetPoint*')()
            all_weights = ROOT.std.vector('Float_t')()

            for entry in hit_container[det_id]:
                all_points.push_back(entry[0])
                all_weights.push_back(entry[1])
            det_hit = ROOT.MTCDetHit(det_id, all_points, all_weights)
            self.det.push_back(det_hit)
            # digi2MCPoints will be added later
            #   for idx, de_value in mc_points[det_id].items():
            #     mc_links.Add(det_id, idx, de_value / norm[det_id])
