""" Conditions Database interface definition """

from abc import ABCMeta, abstractmethod

# Package metadata
__author__    = "Tom Vrancken"
__copyright__ = "TU/e ST2019"
__version__   = "0.3"
__status__    = "Prototype"

ABC = ABCMeta('ABC', (object,), {'__slots__': ()})  # Compatible with python 2 AND 3

### Interface for attaching a database API, this class defines all functions
### that must be available in a concrete implementation of a database API.
class APIInterface(ABC): # For Python 3 we could use 'metaclass=ABCMeta'

    ### Returns a list with all the detector names in the database.
    #   @param detector_id:     (optional) String identifying the parent detector to
    #         retrieve the (sub)detector names for (i.e. 'muonflux/straw_tubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If parent_id does not exist.
    @abstractmethod
    def list_detectors(self, parent_id=None):
        pass

    ### Returns a detector dictionary.
    #   @param  detector_id:    String identifying the detector to retrieve (i.e. 'muonflux/straw_tubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_detector(self, detector_id):
        pass

    ### Adds a new detector to the database.
    #   @param  name:       String specifying the name for the new detector. Must
    #                       be unique. Must not contain a forward slash (i.e. /).
    #   @param  parent_id:  (optional) String identifying the parent detector the
    #                       new detector should be added to as subdetector.
    #   @throw  TypeError:  If input type is not as specified.
    #   @throw  ValueError: If parent_id does not exist.
    @abstractmethod
    def add_detector(self, name, parent_id=None):
        pass

    ### Removes a detector from the database. Caution: all conditions associated
    ### with this detector will be permanently removed as well!
    #   @param  detector_id:    String identifying the detector to remove (i.e.
    #                           'muonflux/straw_tubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def remove_detector(self, detector_id):
        pass

    ### Adds a condition to a detector.
    #   @param  detector_id:    String identifying the detector to which the
    #                           condition will be added (i.e. 'muonflux/straw_tubes').
    #   @param  name:           String specifying the name of the condition (e.g. 'strawPositions').
    #   @param  tag:            String specifying a tag for the condition. Must be unique
    #                           for the same condition name.
    #   @param  collected_at:   Timestamp specifying the date/time the condition was
    #                           acquired. Must be unique w.r.t. the condition name. Can be of type String or datetime.
    #   @param  values:         (optional) Dictionary containing the values of the condition.
    #   @param  type:           (optional) String specifying the type of condition (e.g. 'calibration').
    #   @param  valid_since:    (optional) Timestamp specifying the date/time as of when the
    #                           condition is valid. Can be of type String or datetime.
    #   @param valid_until:     (optional) Timestamp specifying the date/time up
    #                           until the condition is valid. Can be of type String or datetime.
    #   @throw TypeError:       If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def add_condition(self, detector_id, name, tag, collected_at, values=None, type=None, valid_since=None, valid_until=None):
        pass

    ### Returns a list with all conditions associated with a detector.
    #   @param  detector_id:    String identifying the detector for which the
    #                           conditions must be retrieved (i.e. 'muonflux/straw_tubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_conditions(self, detector_id):
        pass

    ### Returns a list with conditions having a specific name for a given detector.
    #   @param  detector_id:    String identifying the detector for which the
    #                           conditions must be retrieved (i.e. 'muonflux/straw_tubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_conditions_by_name(self, detector_id, name):
        pass

    ### Returns a list with conditions associated with a detector that are valid on the
    ### specified date.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/straw_tubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @param  date:           Timestamp specifying a date/time for which conditions must be valid.
    #                           Can be of type String or datetime.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_conditions_by_name_and_validity(self, detector_id, name, date):
        pass

    ### Returns the values of a specific condition belonging to a detector,
    ### identified by condition name and tag.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/straw_tubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @param  tag:            String specifying the tag of the condition to be retrieved.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_condition_by_name_and_tag(self, detector_id, name, tag):
        pass

    ### Returns a list with conditions having a specific tag for a given detector.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/straw_tubes').
    #   @param  tag:            String specifying the tag of the condition to be retrieved.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_conditions_by_tag(self, detector_id, tag):
        pass

    ### Returns the values of a specific condition belonging to a detector, identified by
    ### condition name and collection date/time.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/straw_tubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @param  collected_at:   Timestamp specifying the moment on which the
    #                           condition was collected / measured. This timestamp must be unique w.r.t.
    #                           the condition name. Can be of type String or datetime.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def get_condition_by_name_and_collection_date(self, detector_id, name, collected_at):
        pass

    ### Updates the valid_since and valid_until values of a specific condition
    ### belonging to a detector, identified by condition name and tag.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be updated (i.e. 'muonflux/straw_tubes').
    #   @param  name:           String specifying the name of the conditions to be updated (e.g.
    #                           'strawPositions').
    #   @param  tag:            String specifying the tag of the condition to be updated.
    #   @param  valid_since:    (optional) Timestamp specifying the date/time as of when the
    #                           condition is valid. Can be of type String or datetime.
    #   @param  valid_until:    (optional) Timestamp specifying the date/time up until the
    #                           condition is valid. Can be of type String or datetime.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def update_condition_by_name_and_tag(self, detector_id, name, tag, valid_since=None, valid_until=None):
        pass
