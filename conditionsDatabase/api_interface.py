"""This Module implements a API Interface"""
from abc import ABCMeta, abstractmethod


class APIInterface(metaclass=ABCMeta):
    """
    Interface for attaching a database API, this class defines all functions
    that must be available in a concrete implementation of a database API.
    """

    @abstractmethod
    def get_alignment_data(self, detector_id):
        """
        function get_alignment_data(detectorID) returns alignment data of the specified detector ID
        from the conditions database.
        :param detector_id: The ID of the FairShip detector, for which we want to get Alignment Data
        """

    @abstractmethod
    def set_alignment_data(self, detector_id, alignment_data):
        """
        function set_alignment_data(detector_id, alignment_data) sets the alignment data
        of the specified detector ID from the conditions database.
        :param detector_id: The ID of the FairShip detector, for which we want to set Alignment Data
        :param alignment_data: The alignment data of a certain detector
        """
