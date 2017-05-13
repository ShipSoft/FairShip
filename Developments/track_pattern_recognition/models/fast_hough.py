__author__ = 'Mikhail Hushchyn'

from sklearn.linear_model import LinearRegression
import numpy

############################################## Secondary class #########################################################

class Clusterer(object):

    def __init__(self, x_depth, y_depth, n_min):
        """
        This class divide 2D coordinate space into grid and calculate mass center of hits in the each grid cell.
        This class is used to speed up FastHough track pattern recognition method.

        Parameters
        ----------
        x_depth : int
            Max number of divisions along X-axis. 2^x_depth is number of the grid cells on X-axis.
        y_depth : int
            Max number of divisions along Y-axis. 2^y_depth is number of the grid cells on Y-axis.
        n_min : int
            Min number of hits per one grid cell.
        """

        self.x_depth = x_depth
        self.y_depth = y_depth
        self.n_min = n_min

    @staticmethod
    def clustering(x, indeces, clusters, depth, n_min):
        """
        This function recursively divides 1D array into clusters by dividing each sub-array into 2 parts (tree).

        Parameters
        ----------
        x : array-like
            Array to divide: [x1, x2, ...]
        indeces : array-like
            Indeces of elements of x-array in origin array.
        clusters : array-like
            List of indeces of hits in the clusters.
        depth : int
            Max number of divisions. 2^depth is number of the clusters.
        n_min : int
            Min number of hits per cluster.
        """

        if len(indeces) <= 1 or depth == 0:
            clusters.append(indeces)
            return

        this_x = x[indeces]
        min_x, max_x = this_x.min(), this_x.max()

        if min_x == max_x:
            clusters.append(indeces)
            return

        cut = 0.5 * (min_x + max_x)
        left_inds = indeces[this_x < cut]
        right_inds = indeces[this_x >= cut]

        if len(left_inds) < n_min or len(right_inds) < n_min:
            clusters.append(indeces)
            return
        else:
            Clusterer.clustering(x, left_inds, clusters, depth-1, n_min)
            Clusterer.clustering(x, right_inds, clusters, depth-1, n_min)


    def get_labels(self, clusters, n):
        """
        Estimates cluster_id for each hit.

        Parameters
        ----------
        clusters : array-like
            List of hit indeces in each cluster: [[ind1, ind2, ...], [...], ...]
        n : int
            NUmber of hits.

        Return
        ------
        labels : array-like
            List of cluster_ids.
        """

        labels = -1 * numpy.ones(n)
        cluster_i = 0

        if n == 0 or len(clusters) == 0:
            return labels

        for cl in clusters:
            labels[cl] = cluster_i
            cluster_i += 1

        return labels

    def get_cluster_coord(self, x, clusters):
        """
        Estimates coordinates of mass center of a cluster.

        Parameters
        ----------
        clusters : array-like
            List of hit indeces in each cluster: [[ind1, ind2, ...], [...], ...]
        n : int
            NUmber of hits.

        Return
        ------
        coord : array-like
            List of cluster mass center coordinates.
        """

        coord = []

        for cl in clusters:
            coord.append(x[cl].mean())

        return numpy.array(coord)

    def fit(self, x, y):
        """
        Divide 2D coordinate space into clusters.

        Parameters
        ----------
        x : array-like
            Hit x coordinates: [x1, x2, x3, ...]
        y : array-like
            Hit y coordinates: [y1, y2, y3, ...]

        Use the following attributes as outputs:
            labels_        - list of cluster_ids for the hits
            cluster_x_     - list of x-coordinated of the cluster mass centers
            cluster_y_     - list of y-coordinated of the cluster mass centers
            clusters_      - list of clusters. A cluster is list of hit indeces.
            cluster_x_ids_
        """

        x_clusters = []
        self.clustering(x, numpy.arange(len(x)), x_clusters, self.x_depth, self.n_min)

        clusters = []
        cluster_x_ids = []
        for x_num, x_cluster in enumerate(x_clusters):
            y_clusters = []
            self.clustering(y, x_cluster, y_clusters, self.y_depth, self.n_min)
            clusters += list(y_clusters)
            cluster_x_ids += [x_num] * len(y_clusters)

        self.labels_ = self.get_labels(clusters, len(x))
        self.cluster_x_ = self.get_cluster_coord(x, clusters)
        self.cluster_y_ = self.get_cluster_coord(y, clusters)
        self.clusters_ = clusters
        self.cluster_x_ids_ = cluster_x_ids



################################################## Main class ##########################################################


class FastHough(object):

    def __init__(self,
                 n_tracks=None,
                 min_hits=4,
                 k_size=0.1,
                 b_size=10,
                 k_limits=(-0.3, 0.3),
                 b_limits=(-800, 800),
                 clustering=None,
                 unique_hit_labels=True):
        """
        Track pattern recognition method based on Hough Transform.

        Parameters
        ----------
        n_tracks : int
            Number of tracks to recognize.
        min_hits : int
            Min hits per track to be considered as recognized.
        k_size : int
            Size of k-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        b_size : int
            Size of b-bin in track parameter space (k, b). Track parametrization: y = k * x + b.
        k_limits : tuple
            Tuple (min, max) of min and max allowable k-values.
        b_limits : tuple
            Tuple (min, max) of min and max allowable b-values.
        clustering : object
            Clustering class object to speed up the track recognition.
        unique_hit_labels : boolean
            Is it allowable to take a hit for several tracks of not.
        """


        self.n_tracks = n_tracks
        self.min_hits = min_hits

        self.k_size = k_size
        self.b_size = b_size

        self.k_limits = k_limits
        self.b_limits = b_limits

        self.clustering = clustering
        self.unique_hit_labels = unique_hit_labels

    def transform(self, x, y):
        """
        This function performs fast Hough Transform.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        if self.clustering == None:
            x_clusters = x
            y_clusters = y
            cluster_x_ids = x
        else:
            self.clustering.fit(x, y)
            x_clusters, y_clusters = self.clustering.cluster_x_, self.clustering.cluster_y_
            cluster_x_ids = self.clustering.cluster_x_ids_

        track_inds = []

        for first in range(0, len(x_clusters)-1):
            for second in range(first+1, len(x_clusters)):

                x1, y1, layer1 = x_clusters[first], y_clusters[first], cluster_x_ids[first]
                x2, y2, layer2 = x_clusters[second], y_clusters[second], cluster_x_ids[second]

                if layer1 == layer2:
                   continue

                #if numpy.abs(x1 - x2) <= 100.:
                #    continue

                k = 1. * (y2 - y1) / (x2 - x1)
                b = y1 - k * x1

                if k >= self.k_limits[0] and k <= self.k_limits[1] and b >= self.b_limits[0] and b <= self.b_limits[1]:

                    one_track_inds = self.hits_in_bin(x, y, k, b)
                    one_track_inds1, one_track_inds2 = self.one_hit_per_layer(one_track_inds,
                                                                              x[one_track_inds],
                                                                              y[one_track_inds],
                                                                              x[one_track_inds],
                                                                              k,
                                                                              b)

                    if len(one_track_inds1) >= self.min_hits:
                        track_inds.append(one_track_inds1)

                    if len(one_track_inds2) >= self.min_hits:
                        track_inds.append(one_track_inds2)

        return numpy.array(track_inds)

    def one_hit_per_layer(self, track_inds, x, y, layer, k, b):
        """
        Drop hits from the same layer. In results, only one hit per layer remains.

        Parameters
        ----------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        layer : array-like
            Array of layer ids of hits.
        k : float
            Track parameter: y = k * x + b
        b : float
            Track parameter: y = k * x + b

        Return
        ------
        track_inds1 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        track_inds2 : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """

        new_track_inds1 = []
        new_track_inds2 = []

        diff = numpy.abs(y - (b + k * x))
        sorted_inds = numpy.argsort(diff)
        used1 = []
        used2 = []

        for i in sorted_inds:

            if layer[i] not in used1:
                new_track_inds1.append(track_inds[i])
                used1.append(layer[i])
            elif layer[i] not in used2:
                new_track_inds2.append(track_inds[i])
                used2.append(layer[i])

        return numpy.array(new_track_inds1), numpy.array(new_track_inds2)


    def hits_in_bin(self, x, y, k_bin, b_bin):
        """
        Counts hits in a bin of track parameter space (b, k).

        Parameters
        ---------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        k_bin : float
            Track parameter: y = k_bin * x + b_bin
        b_bin : float
            Track parameter: y = k_bin * x + b_bin

        Return
        ------
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        """


        b_left = y - (k_bin - 0.5 * self.k_size) * x
        b_right = y - (k_bin + 0.5 * self.k_size) * x

        inds = numpy.arange(0, len(x))

        sel = (b_left >= b_bin - 0.5 * self.b_size) * (b_right <= b_bin + 0.5 * self.b_size) + \
              (b_left <= b_bin + 0.5 * self.b_size) * (b_right >= b_bin - 0.5 * self.b_size)

        track_inds = inds[sel]

        return track_inds



    def get_unique_hit_labels(self, track_inds, n_hits):
        """
        Selects the best track candidates. It supposed that a hit can belong to just one track.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        n_hits : int
            Number of hits in an event.

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        new_track_inds = []
        used = numpy.zeros(n_hits)
        n_tracks = 0


        while 1:

            track_lens = numpy.array([len(i[used[i] == 0]) for i in track_inds])

            if len(track_lens) == 0:
                break

            max_len = track_lens.max()

            if max_len < self.min_hits:
                break

            one_track_inds = track_inds[track_lens == track_lens.max()][0]
            one_track_inds = one_track_inds[used[one_track_inds] == 0]

            used[one_track_inds] = 1
            new_track_inds.append(one_track_inds)

            n_tracks += 1
            if self.n_tracks != None and n_tracks >= self.n_tracks:
                break

        return numpy.array(new_track_inds)

    def remove_duplicates(self, track_inds):
        """
        Removes track duplicates.

        Parameters
        ----------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]

        Return
        ------
        track_inds : array-like
            List of recognized tracks. Recognized track is a list of hit indexes correspond to one bin in track parameters space.
            Example: [[ind1, ind2, ind3, ...], [...], ...]
        """

        new_track_inds = []

        if len(track_inds) == 0:
            return numpy.array(new_track_inds)

        sorted_track_inds = [numpy.sort(track) for track in track_inds]

        for first_id in range(len(track_inds)-1):

            counter = 0
            first = sorted_track_inds[first_id]

            for second_id in range(first_id+1, len(track_inds)):

                second = sorted_track_inds[second_id]
                if list(first) == list(second):
                    counter += 1

            if counter == 0:
                new_track_inds.append(first)

        new_track_inds.append(sorted_track_inds[-1])

        return numpy.array(new_track_inds)

    def get_tracks_params(self, x, y, track_inds, sample_weight=None):
        """
        Estimates track parameters y = k * x + b for the recognized tracks.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        track_inds : array-like
            Hit indexes of a track: [ind1, ind2, ...]
        sample_weight : array-like
            Hit weights used during the track fit.

        Return
        ------
        tracks_params : array-like
            Track parameters [k, b].
        """

        tracks_params = []

        if len(track_inds) == 0:
            return []

        for track in track_inds:

            x_track = x[track]
            y_track = y[track]

            if sample_weight != None:
                sample_weight_track = sample_weight[track]
            else:
                sample_weight_track = None

            lr = LinearRegression(copy_X=False)
            lr.fit(x_track.reshape(-1,1), y_track, sample_weight_track)

            params = list(lr.coef_) + [lr.intercept_]
            tracks_params.append(params)

        return numpy.array(tracks_params)


    def fit(self, x, y, sample_weight=None):
        """
        Runs track pattern recognition. Track parametrization: y = k * x + b.

        Parameters
        ----------
        x : array-like
            Array of x coordinates of hits.
        y : array-like
            Array of x coordinates of hits.
        sample_weight : array-like
            Hit weights used during the track fit.
        """

        track_inds = self.transform(x, y)

        if self.unique_hit_labels:
            self.track_inds_ = self.get_unique_hit_labels(track_inds, len(x))
        else:
            self.track_inds_ = self.remove_duplicates(track_inds)

        self.tracks_params_ = self.get_tracks_params(x, y, self.track_inds_, sample_weight)

