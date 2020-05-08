""" Conditions Database interface definition. """
from abc import ABCMeta, abstractmethod
from datetime import datetime
## As of Python 3.8 we can do more with typing. It is recommended to make
## the API interface class final. Use the following import and provided
## decorator for the class.
#from typing import final


# Package metadata
__author__    = "Tom Vrancken"
__email__     = "dev@tomvrancken.nl"
__copyright__ = "TU/e ST2019"
__credits__   = ["Juan van der Heijden", "Georgios Azis"]
__version__   = "1.0"
__status__    = "Prototype"


_ABC = ABCMeta('ABC', (object,), {'__slots__': ()})  # Compatible with python 2 AND 3

### Conditions Database Interface definition. This class defines the interface that all
### storage back-end adapters must implement.
#TODO uncomment for python >= 3.8: @final
class APIInterface(_ABC): # For Python 3 we could/should use 'metaclass=ABCMeta'

    ### Returns a list with all the detector names in the database.
    #   @param detector_id:     (optional) String identifying the parent detector to
    #                           retrieve the (sub)detector names for
    #                           (i.e. 'muonflux/driftTubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If parent_id does not exist.
    #   @retval List:           A list with (string) names of detectors under the specified parent.
    @abstractmethod
    def list_detectors(self, parent_id=None):
        pass

    ### Returns a detector dictionary.
    #   @param  detector_id:    String identifying the detector to retrieve
    #                           (i.e. 'muonflux/driftTubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval Dict:           A dictionary adhering to the following specification:
    #                           Detector = { 'name': String, 'subdetectors': List of Detector,
    #                                        'conditions': List of Condition }
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
    #                           'muonflux/driftTubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def remove_detector(self, detector_id):
        pass

    ### Adds a condition to a detector.
    #   @param  detector_id:    String identifying the detector to which the
    #                           condition will be added (i.e. 'muonflux/driftTubes').
    #   @param  name:           String specifying the name of the condition (e.g. 'strawPositions').
    #   @param  tag:            String specifying a tag for the condition. Must be unique
    #                           for the same condition name.
    #   @param  values:         The values of the condition. Can be any data type.
    #   @param  type:           (optional) String specifying the type of condition (e.g. 'calibration').
    #   @param  collected_at:   (optional) Timestamp specifying the date/time the condition was
    #                           acquired. Must be unique w.r.t. the condition name.
    #                           Can be of type String or datetime. This timestamp will be stored
    #                           with an accuracy up to seconds.
    #                           If unspecified, this value will be set to 'datetime.now'.
    #   @param  valid_since:    (optional) Timestamp specifying the date/time as of when the
    #                           condition is valid. Can be of type String or datetime. This
    #                           timestamp will be stored with an accuracy up to seconds.
    #                           If unspecified, this value will be set to 'datetime.now'.
    #   @param valid_until:     (optional) Timestamp specifying the date/time up
    #                           until the condition is valid. Can be of type String or datetime.
    #                           If unspecified, this value will be set to 'datetime.max'. This
    #                           timestamp will be stored with an accuracy up to seconds.
    #   @throw TypeError:       If input type is not as specified.
    #   @throw ValueError:      If detector_id does not exist.
    @abstractmethod
    def add_condition(self, detector_id, name, tag, values, type=None,
                      collected_at=datetime.now(), valid_since=datetime.now(),
                      valid_until=datetime.max):
        pass

    ### Returns a list with all condition dictionaries associated with a detector.
    #   @param  detector_id:    String identifying the detector for which the
    #                           conditions must be retrieved (i.e. 'muonflux/driftTubes').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval List:           A list with condition dictionaries adhering to the following
    #                           specification:
    #                           Condition = { 'name': String, 'tag': String, 'type': String,
    #                                         'collected_at': datetime, 'valid_since': datetime,
    #                                         'valid_until': datetime, 'values': mixed }
    @abstractmethod
    def get_conditions(self, detector_id):
        pass

    ### Returns a list with condition dictionaries having a specific name for a given detector.
    #   @param  detector_id:    String identifying the detector for which the
    #                           conditions must be retrieved (i.e. 'muonflux/driftTubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval List:           A list with condition dictionaries adhering to the following
    #                           specification:
    #                           Condition = { 'name': String, 'tag': String, 'type': String,
    #                                         'collected_at': datetime, 'valid_since': datetime,
    #                                         'valid_until': datetime, 'values': mixed }
    @abstractmethod
    def get_conditions_by_name(self, detector_id, name):
        pass

    ### Returns a list with condition dictionaries having a specific tag for a given detector.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/driftTubes').
    #   @param  tag:            String specifying the tag of the condition to be retrieved.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval List:           A list with condition dictionaries adhering to the following
    #                           specification:
    #                           Condition = { 'name': String, 'tag': String, 'type': String,
    #                                         'collected_at': datetime, 'valid_since': datetime,
    #                                         'valid_until': datetime, 'values': mixed }
    @abstractmethod
    def get_conditions_by_tag(self, detector_id, tag):
        pass

    ### Returns a list with condition dictionaries associated with a detector that are valid on the
    ### specified date.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/driftTubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @param  start_date:     Timestamp specifying a start of a date/time range for which
    #                           conditions must be valid.
    #                           Can be of type String or datetime.
    #   @param  end_date:       (optional) Timestamp specifying the end of a date/time range for
    #                           which conditions must be valid.
    #                           If not specified then we will query for validity on the start_date.
    #                           Can be of type String or datetime
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval List:           A list with condition dictionaries adhering to the following
    #                           specification:
    #                           Condition = { 'name': String, 'tag': String, 'type': String,
    #                                         'collected_at': datetime, 'valid_since': datetime,
    #                                         'valid_until': datetime, 'values': mixed }
    @abstractmethod
    def get_conditions_by_name_and_validity(self, detector_id, name, start_date, end_date=None):
        pass

    ### Returns a condition dictionary of a specific condition belonging to a detector,
    ### identified by condition name and tag. This combination must be unique.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/driftTubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @param  tag:            String specifying the tag of the condition to be retrieved.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval Dict:           A dictionary adhering to the following specification:
    #                           Condition = { 'name': String, 'tag': String, 'type': String,
    #                                         'collected_at': datetime, 'valid_since': datetime,
    #                                         'valid_until': datetime, 'values': mixed }
    @abstractmethod
    def get_condition_by_name_and_tag(self, detector_id, name, tag):
        pass

    ### Returns a condition dictionary of a specific condition belonging to a detector, identified
    ### by condition name and collection date/time. This combination must be unique.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be retrieved (i.e. 'muonflux/driftTubes').
    #   @param  name:           String specifying the name of the conditions to be retrieved (e.g.
    #                           'strawPositions').
    #   @param  collected_at:   Timestamp specifying the moment on which the condition was
    #                           collected/measured. Can be of type String or datetime.
    #                           Collection dates are stored with accuracy up to seconds.
    #
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    #   @retval Dict:           A dictionary adhering to the following specification:
    #                           Condition = { 'name': String, 'tag': String, 'type': String,
    #                                         'collected_at': datetime, 'valid_since': datetime,
    #                                         'valid_until': datetime, 'values': mixed }
    @abstractmethod
    def get_condition_by_name_and_collection_date(self, detector_id, name, collected_at):
        pass

    ### Updates the type, valid_since and valid_until values of a specific condition
    ### belonging to a detector, identified by condition name and tag.
    #   @param  detector_id:    String identifying the detector for which the
    #                           condition must be updated (i.e. 'muonflux/driftTubes').
    #   @param  name:           String specifying the name of the conditions to be updated (e.g.
    #                           'strawPositions').
    #   @param  tag:            String specifying the tag of the condition to be updated.
    #   @param  type:           (optional) String specifying the type of condition
    #                           (e.g. 'calibration').
    #   @param  valid_since:    (optional) Timestamp specifying the date/time as of when the
    #                           condition is valid. Can be of type String or datetime.
    #   @param  valid_until:    (optional) Timestamp specifying the date/time up until the
    #                           condition is valid. Can be of type String or datetime.
    #   @throw  TypeError:      If input type is not as specified.
    #   @throw  ValueError:     If detector_id does not exist.
    @abstractmethod
    def update_condition_by_name_and_tag(self, detector_id, name, tag,
                                         type=None, valid_since=None, valid_until=None):
        pass
