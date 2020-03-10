""" Conditions Database interface definition """

from abc import ABCMeta, abstractmethod

# Package metadata
__author__    = "Tom Vrancken"
__copyright__ = "TU/e ST2019"
__version__   = "0.2"
__status__    = "Prototype"

ABC = ABCMeta('ABC', (object,), {'__slots__': ()})  # Compatible with python 2 AND 3


class APIInterface(ABC): # For Python 3 we could use 'metaclass=ABCMeta'
    """
    Interface for attaching a database API, this class defines all functions
    that must be available in a concrete implementation of a database API.
    """

    @abstractmethod
    def list_detectors(self, parent_id):
        """
        Returns a list with all the detector names in the database.

        :param detector_id: (optional) String identifying the parent detector to
        retrieve the (sub)detector names for (i.e. 'muonflux/straw_tubes').
        """

    @abstractmethod
    def get_detector(self, detector_id):
        """
        Returns a detector dictionary.

        :param detector_id: String identifying the detector to retrieve (i.e.
        'muonflux/straw_tubes').
        """

    @abstractmethod
    def add_detector(self, name, parent_id):
        """
        Adds a new detector to the database.

        :param name: String specifying the name for the new detector. Must
        be unique. Must not contain a forward slash (i.e. /).
        :param parent_id: (optional) String identifying the parent detector the
        new detector should be added to as subdetector.
        """

    @abstractmethod
    def remove_detector(self, detector_id):
        """
        Removes a detector from the database. Caution: all conditions associated
        with this detector will be permanently removed as well!

        :param detector_id: String identifying the detector to remove (i.e.
        'muonflux/straw_tubes').
        """

    @abstractmethod
    def add_condition(self, detector_id, name, values, type, tag, collected_at, valid_since, valid_until):
        """
        Adds a condition to a detector.

        :param detector_id: String identifying the detector to which the
        condition will be added (i.e. 'muonflux/straw_tubes').
        :param name: String specifying the name of the condition (e.g. 'strawPositions').
        :param values: Dictionary containing the values of the condition.
        :param type: String specifying the type of condition (e.g. 'calibration').
        :param tag: String specifying a tag for the condition. Must be unique
        for the same condition name.
        :param collected_at: Timestamp specifying the date/time the condition
        was acquired. Must be unique w.r.t. the condition name.
        :param valid_since: Timestamp specifying the date/time as of when the
        condition is valid.
        :param valid_until: Timestamp specifying the date/time up until the
        condition is valid.
        """

    @abstractmethod
    def get_conditions(self, detector_id):
        """
        Returns a list with all conditions associated with a detector.

        :param detector_id: String identifying the detector for which the
        conditions must be retrieved (i.e. 'muonflux/straw_tubes').
        """

    @abstractmethod
    def get_conditions_by_name(self, detector_id, name):
        """
        Returns a list with conditions having a specific name for a given detector.

        :param detector_id: String identifying the detector for which the
        condition must be retrieved (i.e. 'muonflux/straw_tubes').
        :param name: String specifying the name of the conditions to be retrieved (e.g.
        'strawPositions').
        """

    @abstractmethod
    def get_conditions_by_name_and_validity(self, detector_id, name, date):
        """
        Returns a list with conditions associated with a detector that are valid on the
        specified date.

        :param detector_id: String identifying the detector for which the
        condition must be retrieved (i.e. 'muonflux/straw_tubes').
        :param name: String specifying the name of the conditions to be retrieved (e.g.
        'strawPositions').
        :param date: Timestamp specifying a date/time for which conditions must be valid.
        """

    @abstractmethod
    def get_condition_by_name_and_tag(self, detector_id, name, tag):
        """
        Returns the values of a specific condition belonging to a detector,
        identified by condition name and tag.

        :param detector_id: String identifying the detector for which the
        condition must be retrieved (i.e. 'muonflux/straw_tubes').
        :param name: String specifying the name of the condition to be retrieved (e.g.
        'strawPositions').
        :param tag: String specifying the tag of the condition to be retrieved.
        """

    @abstractmethod
    def get_condition_by_name_and_collection_date(self, detector_id, name, collected_at):
        """
        Returns the values of a specific condition belonging to a detector, identified by
        condition name and collection date/time.

        :param detector_id: String identifying the detector for which the
        condition must be retrieved (i.e. 'muonflux/straw_tubes').
        :param name: String specifying the name of the condition to be retrieved (e.g.
        'strawPositions').
        :param collected_at: Timestamp specifying the moment on which the
        condition was collected / measured. This timestamp must be unique w.r.t.
        the condition name.
        """
