__author__ = 'Mikhail Hushchyn'

import numpy
import pandas


class Combinator(object):

    def __init__(self, z_magnet=3070., magnetic_field=-0.75, dy_max=2., dx_max=20.):
        """
        This class combines tracks before and after the magnet,
        estimates a particles charge and momentum based on its deflection in the magnetic field.

        Parameters
        ----------
        z_magnet : float,
            Z-coordinate of the center of the magnet.
        magnetic_field : float,
            Inductivity of the magnetic field.
        dy_max : float,
            Max distance on y between the tracks before and after the magnet in center of the magnet.
        dx_max : float,
            Max distance on x between the tracks before and after the magnet in center of the magnet.
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
        This function finds combinations of two tracks befor and after the magnet.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.

        Return
        ------
        List of [track_id_before, track_id_after] for the track combinations.
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


                if dy <= dy_max and dx <= dx_max:

                    self.dx.append(x_after - x_before)
                    self.dy.append(y_after - y_before)

                    tracks_combinations.append(numpy.array([track_id_before, track_id_after]))
                    #continue

        return numpy.array(tracks_combinations)

    def get_charges(self, tracks_before, tracks_after, tracks_combinations):
        """
        This function estimates charges of particles.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.
        tracks_combinations : array-like,
            List of [track_id_before, track_id_after], indexes of the tracks in the combinations.

        Return
        ------
        List of estimated charges for the track combinations: [q1, q2, ...]
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
        This function estimates momentum values of particles.

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.
        tracks_combinations : array-like,
            List of [track_id_before, track_id_after], indexes of the tracks in the combinations.

        Return
        ------
        List of estimated inverse momentum values for the track combinations: [pinv1, pinv2, ...]
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

        Parameters
        ----------
        tracks_before : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track before the magnet.
            Track parametrization is y = kx + b.
        tracks_after : array-like,
            List of [[k_yz, b_yz], [k_xz, b_xz]], parameters of a track after the magnet.
            Track parametrization is y = kx + b.

        Use the following attributes as outputs:
            tracks_combinations_
            charges_
            inv_momentums_
        """

        tracks_combinations = self.get_tracks_combination(tracks_before, tracks_after)
        charges = self.get_charges(tracks_before, tracks_after, tracks_combinations)
        inv_momentums = self.get_inv_momentums(tracks_before, tracks_after, tracks_combinations)


        # Use these attributes as outputs
        self.tracks_combinations_ = tracks_combinations
        self.charges_ = charges
        self.inv_momentums_ = inv_momentums