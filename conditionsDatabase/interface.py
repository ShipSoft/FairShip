"""This Module implements a API Interface"""
from abc import ABCMeta, abstractmethod

ABC = ABCMeta('ABC', (object,), {'__slots__': ()})  # Compatible with python 2 AND 3


class APIInterface(ABC): # For Python 3 we could use 'metaclass=ABCMeta'
    """
    Interface for attaching a database API, this class defines all functions
    that must be available in a concrete implementation of a database API.
    """

    @abstractmethod
    def get_position_measurements(self, detector_id):
        """
        Returns a list with position measurements for @detector_id.
        
        :param detector_id: String identifying the detector to retrieve the position measurements from (i.e. 'muonflux/straw_tubes').
        """

    @abstractmethod
    def add_position_measurements(self, detector_id, measurements):
        """
        Adds a list with position measurements to @detector_id.

        :param detector_id: String identifying the detector to set the position measurements for (i.e. 'muonflux/straw_tubes').
        :param measurements: List specifying the straw positions that need to be added for this @detetector_id.
        """

    @abstractmethod
    def get_straw_positions(self, detector_id):
        """
        Returns a list with straw positions for @detector_id.
        
        :param detector_id: String identifying the detector to retrieve the straw positions from (i.e. 'muonflux/straw_tubes').
        """
    
    @abstractmethod
    def add_straw_positions(self, detector_id, positions):
        """
        Adds a list with straw positions to @detector_id.
        
        :param detector_id: String identifying the detector to set the straw positions for (i.e. 'muonflux/straw_tubes').
        :param positions: List specifying the straw positions that need to be added for this @detetector_id.
        """
    
    @abstractmethod
    def get_alignment_corrections(self, detector_id):
        """
        Returns a list with alignment corrections for @detector_id.
        
        :param detector_id: String identifying the detector to retrieve the alignment corrections from (i.e. 'muonflux/straw_tubes').
        """
    
    @abstractmethod
    def add_alignment_corrections(self, detector_id, corrections):
        """
        Adds a list with alignment corrections to @detector_id.
        
        :param detector_id: String identifying the detector to set the straw positions for (i.e. 'muonflux/straw_tubes').
        :param corrections: List specifying the alignment corrections that need to be added for this @detetector_id.
        """
