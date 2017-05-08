__author__ = 'Mikhail Hushchyn'

from sklearn.linear_model import LinearRegression
import numpy


class Clusterer(object):

    def __init__(self, x_depth, y_depth, n_min):

        self.x_depth = x_depth
        self.y_depth = y_depth
        self.n_min = n_min
        pass

    @staticmethod
    def clustering(x, indeces, clusters, depth, n_min):

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

        labels = -1 * numpy.ones(n)
        cluster_i = 0

        if n == 0 or len(clusters) == 0:
            return labels

        for cl in clusters:
            labels[cl] = cluster_i
            cluster_i += 1

        return labels

    def get_cluster_coord(self, x, clusters):

        coord = []

        for cl in clusters:
            coord.append(x[cl].mean())

        return numpy.array(coord)

    def fit(self, x, y):

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


class FastHough(object):

    def __init__(self, n_tracks=None, min_hits=4, k_size=0.1, b_size=10, k_limits=(-0.3, 0.3), b_limits=(-800, 800), clustering=None, unique_hit_labels=True):


        self.n_tracks = n_tracks
        self.min_hits = min_hits

        self.k_size = k_size
        self.b_size = b_size

        self.k_limits = k_limits
        self.b_limits = b_limits

        self.clustering = clustering
        self.unique_hit_labels = unique_hit_labels

    def transform(self, x, y):

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

                k = 1. * (y2 - y1) / (x2 - x1)
                b = y1 - k * x1

                if k >= self.k_limits[0] and k <= self.k_limits[1] and b >= self.b_limits[0] and b <= self.b_limits[1]:

                    one_track_inds = self.hits_in_bin(x, y, k, b)

                    if len(one_track_inds) >= self.min_hits:
                        track_inds.append(one_track_inds)

        return numpy.array(track_inds)


    def hits_in_bin(self, x, y, k_bin, b_bin):


        b_left = y - (k_bin - 0.5 * self.k_size) * x
        b_right = y - (k_bin + 0.5 * self.k_size) * x

        inds = numpy.arange(0, len(x))

        sel = (b_left >= b_bin - 0.5 * self.b_size) * (b_right <= b_bin + 0.5 * self.b_size) + \
              (b_left <= b_bin + 0.5 * self.b_size) * (b_right >= b_bin - 0.5 * self.b_size)

        track_inds = inds[sel]

        return track_inds



    def get_unique_hit_labels(self, track_inds, n_hits):

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

        track_inds = self.transform(x, y)

        if self.unique_hit_labels:
            self.track_inds_ = self.get_unique_hit_labels(track_inds, len(x))
        else:
            self.track_inds_ = self.remove_duplicates(track_inds)

        self.tracks_params_ = self.get_tracks_params(x, y, self.track_inds_, sample_weight)

