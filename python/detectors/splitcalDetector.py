from math import fabs

import ROOT
from BaseDetector import BaseDetector


class splitcalDetector(BaseDetector):
    def __init__(self, name, intree, model):
        # Initialize base class for digitized hits
        super().__init__(name, intree, model, "Splitcal")

        # Clusters use value storage
        self.reco = ROOT.std.vector("splitcalCluster")()
        # Register cluster field with model
        self.reco_field_name = "Reco_SplitcalClusters"
        self.model.MakeField["std::vector<splitcalCluster>"](self.reco_field_name)

    def delete(self):
        # Override to also clear reconstruction branch
        super().delete()
        self.reco.clear()

    def fill(self, entry):
        """Fill detector hit and cluster fields into RNTuple entry.

        Args:
            entry: RNTuple entry to fill
        """
        # Fill hit field
        super().fill(entry)
        # Fill cluster field
        if self.reco_field_name:
            entry[self.reco_field_name] = self.reco

    def digitize(self):
        """Digitize splitcal hits and perform cluster reconstruction."""
        # Digitization: group MC points by detector cell, then create one hit per cell
        points_by_detID = {}
        for point in self.intree.splitcalPoint:
            detector_id = point.GetDetectorID()
            if detector_id not in points_by_detID:
                points_by_detID[detector_id] = []
            points_by_detID[detector_id].append(point)

        # Create one hit per detector cell from all points in that cell
        for detector_id, points in points_by_detID.items():
            # Convert Python list to std::vector for C++
            point_vector = ROOT.std.vector("splitcalPoint")()
            for point in points:
                point_vector.push_back(point)

            hit = ROOT.splitcalHit(point_vector, self.intree.t0)
            self.det.push_back(hit)

        # Cluster reconstruction
        self._reconstruct_clusters()

    def _reconstruct_clusters(self):
        """Perform cluster reconstruction from digitized hits."""
        # Hit selection: select hits above noise threshold
        noise_energy_threshold = 0.002  # GeV
        list_hits_above_threshold = []
        hit_to_index = {}
        for idx, hit in enumerate(self.det):
            if hit.GetEnergy() > noise_energy_threshold:
                hit.SetIsUsed(0)
                list_hits_above_threshold.append(hit)
                hit_to_index[id(hit)] = idx

        if not list_hits_above_threshold:
            return

        # Step 1: group of neighbouring cells
        self.step = 1
        self.input_hits = list_hits_above_threshold
        list_clusters_of_hits = self._clustering()

        # Step 2: check if clusters can be split in XZ and YZ planes
        self.step = 2
        list_final_clusters = {}
        index_final_cluster = 0

        for i in list_clusters_of_hits:
            list_hits_x = []
            list_hits_y = []
            for hit in list_clusters_of_hits[i]:
                hit.SetIsUsed(0)
                if hit.IsX():
                    list_hits_x.append(hit)
                if hit.IsY():
                    list_hits_y.append(hit)

            # Re-cluster in XZ plane
            self.input_hits = list_hits_x
            list_subclusters_of_x_hits = self._clustering()
            cluster_energy_x = self._get_cluster_energy(list_hits_x)

            self.list_subclusters_of_hits = list_subclusters_of_x_hits
            list_of_subclusters_x = self._get_subclusters_excluding_fragments()

            # Compute energy weights from X splitting
            weights_from_x_splitting = {}
            for index_subcluster in list_of_subclusters_x:
                subcluster_energy_x = self._get_cluster_energy(list_of_subclusters_x[index_subcluster])
                weight = subcluster_energy_x / cluster_energy_x if cluster_energy_x > 0 else 0
                weights_from_x_splitting[index_subcluster] = weight

            # Re-cluster in YZ plane
            self.input_hits = list_hits_y
            list_subclusters_of_y_hits = self._clustering()
            cluster_energy_y = self._get_cluster_energy(list_hits_y)

            self.list_subclusters_of_hits = list_subclusters_of_y_hits
            list_of_subclusters_y = self._get_subclusters_excluding_fragments()

            # Compute energy weights from Y splitting
            weights_from_y_splitting = {}
            for index_subcluster in list_of_subclusters_y:
                subcluster_energy_y = self._get_cluster_energy(list_of_subclusters_y[index_subcluster])
                weight = subcluster_energy_y / cluster_energy_y if cluster_energy_y > 0 else 0
                weights_from_y_splitting[index_subcluster] = weight

            # Build final clusters
            if len(list_of_subclusters_x) == 1 and len(list_of_subclusters_y) == 1:
                list_final_clusters[index_final_cluster] = [(hit, 1.0) for hit in list_clusters_of_hits[i]]
                index_final_cluster += 1
            else:
                for ix in list_of_subclusters_x:
                    for iy in list_of_subclusters_y:
                        # Build list of (hit, weight) tuples
                        hit_weight_list = []
                        for hit in list_of_subclusters_y[iy]:
                            hit_weight_list.append((hit, weights_from_x_splitting[ix]))
                        for hit in list_of_subclusters_x[ix]:
                            hit_weight_list.append((hit, weights_from_y_splitting[iy]))

                        list_final_clusters[index_final_cluster] = hit_weight_list
                        index_final_cluster += 1

        # Fill cluster objects
        for i in list_final_clusters:
            # Create empty cluster
            cluster = ROOT.splitcalCluster()

            # Add all hits with their weights using indices
            for hit, weight in list_final_clusters[i]:
                hit_index = hit_to_index[id(hit)]
                cluster.AddHit(hit_index, weight)

            cluster.SetIndex(int(i))
            cluster.ComputeEtaPhiE(self.det)
            self.reco.push_back(cluster)

    def _get_subclusters_excluding_fragments(self):
        """Merge fragments into the closest subcluster."""
        list_subclusters_excluding_fragments = {}
        fragment_indices = []
        subclusters_indices = []

        for k in self.list_subclusters_of_hits:
            subcluster_size = len(self.list_subclusters_of_hits[k])
            if subcluster_size < 5:
                fragment_indices.append(k)
            else:
                subclusters_indices.append(k)

        # Merge all fragments if no subclusters exist
        if len(subclusters_indices) == 0 and len(fragment_indices) != 0:
            subclusters_indices.append(0)

        # Merge fragments into closest subcluster
        for index_fragment in fragment_indices:
            minDistance = -1
            minIndex = -1
            first_hit_fragment = self.list_subclusters_of_hits[index_fragment][0]

            for index_subcluster in subclusters_indices:
                first_hit_subcluster = self.list_subclusters_of_hits[index_subcluster][0]
                if first_hit_fragment.IsX():
                    distance = fabs(first_hit_fragment.GetX() - first_hit_subcluster.GetX())
                else:
                    distance = fabs(first_hit_fragment.GetY() - first_hit_subcluster.GetY())

                if minDistance < 0 or distance < minDistance:
                    minDistance = distance
                    minIndex = index_subcluster

            if minIndex != index_fragment:
                self.list_subclusters_of_hits[minIndex] += self.list_subclusters_of_hits[index_fragment]

        for counter, index_subcluster in enumerate(subclusters_indices):
            list_subclusters_excluding_fragments[counter] = self.list_subclusters_of_hits[index_subcluster]

        return list_subclusters_excluding_fragments

    def _get_cluster_energy(self, list_hits):
        """Calculate total energy of hits in a cluster."""
        energy = 0
        for hit in list_hits:
            energy += hit.GetEnergy()
        return energy

    def _clustering(self):
        """Perform clustering algorithm on input hits."""
        list_hits_in_cluster = {}
        cluster_index = -1

        for i, hit in enumerate(self.input_hits):
            if hit.IsUsed() == 1:
                continue

            neighbours = self._get_neighbours(hit)

            if len(neighbours) < 1:
                continue

            cluster_index = cluster_index + 1
            hit.SetIsUsed(1)
            list_hits_in_cluster[cluster_index] = []
            list_hits_in_cluster[cluster_index].append(hit)

            for neighbouringHit in neighbours:
                if neighbouringHit.IsUsed() == 1:
                    continue

                neighbouringHit.SetIsUsed(1)
                list_hits_in_cluster[cluster_index].append(neighbouringHit)

                expand_neighbours = self._get_neighbours(neighbouringHit)

                if len(expand_neighbours) >= 1:
                    for additionalHit in expand_neighbours:
                        if additionalHit not in neighbours:
                            neighbours.append(additionalHit)

        return list_hits_in_cluster

    def _get_neighbours(self, hit):
        """Find neighbouring hits for clustering."""
        list_neighbours = []
        err_x_1 = hit.GetXError()
        err_y_1 = hit.GetYError()
        err_z_1 = hit.GetZError()

        # Allow one or more 'missing' hit in x/y
        max_gap = 2.0
        if hit.IsX():
            err_x_1 = err_x_1 * max_gap
        if hit.IsY():
            err_y_1 = err_y_1 * max_gap

        for hit2 in self.input_hits:
            if hit2 is not hit:
                Dx = fabs(hit2.GetX() - hit.GetX())
                Dy = fabs(hit2.GetY() - hit.GetY())
                Dz = fabs(hit2.GetZ() - hit.GetZ())
                err_x_2 = hit2.GetXError()
                err_y_2 = hit2.GetYError()
                err_z_2 = hit2.GetZError()

                if hit2.IsX():
                    err_x_2 = err_x_2 * max_gap
                if hit2.IsY():
                    err_y_2 = err_y_2 * max_gap

                if self.step == 1:
                    if hit.IsX():
                        if (
                            Dx <= (err_x_1 + err_x_2)
                            and Dz <= 2 * (err_z_1 + err_z_2)
                            and ((Dy <= (err_y_1 + err_y_2) and Dz > 0.0) or (Dy == 0))
                        ):
                            list_neighbours.append(hit2)
                    if hit.IsY():
                        if (
                            Dy <= (err_y_1 + err_y_2)
                            and Dz <= 2 * (err_z_1 + err_z_2)
                            and ((Dx <= (err_x_1 + err_x_2) and Dz > 0.0) or (Dx == 0))
                        ):
                            list_neighbours.append(hit2)

                elif self.step == 2:
                    # Relax z condition for step 2
                    if hit.IsX():
                        if (
                            Dx <= (err_x_1 + err_x_2)
                            and Dz <= 6 * (err_z_1 + err_z_2)
                            and ((Dy <= (err_y_1 + err_y_2) and Dz > 0.0) or (Dy == 0))
                        ):
                            list_neighbours.append(hit2)
                    if hit.IsY():
                        if (
                            Dy <= (err_y_1 + err_y_2)
                            and Dz <= 6 * (err_z_1 + err_z_2)
                            and ((Dx <= (err_x_1 + err_x_2) and Dz > 0.0) or (Dx == 0))
                        ):
                            list_neighbours.append(hit2)
                else:
                    print("-- _get_neighbours: ERROR: step not defined")

        return list_neighbours
