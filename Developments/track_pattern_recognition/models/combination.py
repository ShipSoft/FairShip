__author__ = 'Mikhail Hushchyn'

import numpy
import pandas


class Combinator(object):

    def __init__(self, z_magnet=3070., magnetic_field=-0.75, dy_max=2., dx_max=20.):
        """
        This class combines tracks before and after the magnet,
        estimates a particles charge and momentim based on its deflection in the magnetic field.
        :param z_magnet: floaf, z-coordinate of the center of the magnet.
        :param magnetic_field: float, inductivity of the magnetic field.
        :param dy_max: float, max distance on y between the tracks before and after the magnet in center of the magnet.
        :param dx_max: float, max distance on x between the tracks before and after the magnet in center of the magnet.
        :return:
        """

        self.z_magnet = z_magnet
        self.magnetic_field = magnetic_field
        self.dy_max = dy_max
        self.dx_max = dx_max

        self.tracks_combinations_ = None
        self.charges_ = None
        self.inv_momentums_ = None

    def get_tracks_combination(self, tracks_before, tracks_after):
        """
        This function combines the two tracks.
        :param tracks_before: list of [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track before the magnet. y = kx + b.
        :param tracks_after: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track after the magnet. y = kx + b.
        :return: list of [track_id_before, track_id_after]
        """

        z_magnet = self.z_magnet
        dy_max = self.dy_max
        dx_max = self.dx_max

        self.dx = []
        self.dy = []

        tracks_combinations = []

        for track_id_before, one_track_before in enumerate(tracks_before):

            for track_id_after, one_track_after in enumerate(tracks_after):


                if len(one_track_before[1])==0 or len(one_track_after[1])==0:
                    continue

                y_before = z_magnet * one_track_before[0][0] + one_track_before[0][1]
                x_before = z_magnet * one_track_before[1][0] + one_track_before[1][1]

                y_after = z_magnet * one_track_after[0][0] + one_track_after[0][1]
                x_after = z_magnet * one_track_after[1][0] + one_track_after[1][1]

                dy = numpy.abs(y_after - y_before)
                dx = numpy.abs(x_after - x_before)
                dr = numpy.sqrt(dy**2 + dx**2)

                #print dy, dx


                if dy <= dy_max and dx <= dx_max:

                    self.dx.append(x_after - x_before)
                    self.dy.append(y_after - y_before)

                    tracks_combinations.append(numpy.array([track_id_before, track_id_after]))
                    #continue

        return numpy.array(tracks_combinations)

    def get_charges(self, tracks_before, tracks_after, tracks_combinations):
        """
        This function estimates the charges of the particles.
        :param tracks_before: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track before the magnet. y = kx + b.
        :param tracks_after: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track after the magnet. y = kx + b.
        :param tracks_combinations: list of [track_id_before, track_id_after], indexes of the tracks.
        :return: list if estimated charges
        """

        charges = []

        for one_tracks_combination in tracks_combinations:

            one_track_before = tracks_before[one_tracks_combination[0]]
            one_track_after = tracks_after[one_tracks_combination[1]]

            k_yz_before = one_track_before[0][0]
            k_yz_after = one_track_after[0][0]

            difftan = (k_yz_before - k_yz_after) / (1. + k_yz_before * k_yz_after)


            if difftan > 0:

                one_charge = -1.

            else:

                one_charge = 1.


            charges.append(one_charge)

        return numpy.array(charges)


    def get_inv_momentums(self, tracks_before, tracks_after, tracks_combinations):
        """
        This function estimates the momentums of the particles.
        :param tracks_before: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track before the magnet. y = kx + b.
        :param tracks_after: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track after the magnet. y = kx + b.
        :param tracks_combinations: list of [track_id_before, track_id_after], indexes of the tracks.
        :return: list if estimated inverse momentums.
        """

        Bm = self.magnetic_field
        inv_momentums = []

        for one_tracks_combination in tracks_combinations:

            one_track_before = tracks_before[one_tracks_combination[0]]
            one_track_after = tracks_after[one_tracks_combination[1]]

            k_yz_before = one_track_before[0][0]
            k_yz_after = one_track_after[0][0]

            a = numpy.arctan(k_yz_before)
            b = numpy.arctan(k_yz_after)
            pinv = numpy.sin(a - b) / (0.3 * Bm)

            #pinv = numpy.abs(pinv) # !!!!

            inv_momentums.append(pinv)


        return numpy.array(inv_momentums)


    def combine(self, tracks_before, tracks_after):
        """
        Run the combinator.
        :param tracks_before: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track before the magnet. y = kx + b.
        :param tracks_after: list, [[k_yz, b_yz], [k_xz, b_xz]], parameters of the track after the magnet. y = kx + b.
        :return:
        """

        tracks_combinations = self.get_tracks_combination(tracks_before, tracks_after)
        charges = self.get_charges(tracks_before, tracks_after, tracks_combinations)
        inv_momentums = self.get_inv_momentums(tracks_before, tracks_after, tracks_combinations)


        self.tracks_combinations_ = tracks_combinations
        self.charges_ = charges
        self.inv_momentums_ = inv_momentums