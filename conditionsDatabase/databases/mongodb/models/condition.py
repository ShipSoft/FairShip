"""
@package conditionsDatabase
Contains a Mongo Engine model definition for a Condition
"""
from mongoengine import EmbeddedDocument, DictField, StringField, ComplexDateTimeField

class Condition(EmbeddedDocument):
    """
    This model represents meta-data about an experiment describing a specific (set of)
    value(s) (i.e. a condition under which an experiment took place) at a date/time
    when the condition was measured/collected. Conditions are associated with a Detector.

    :param: collected_at - the date/time that the condition was collected; should not be empty
    :param: name - name of a condition
    :param: tag - tag of a condition
    :param: type - type of a condition; should not be empty
    :param: valid_since - the date/time that the values started to be valid
    :param: valid_until - the date/time that the values become invalid
    :param: values - dictionary of values
    """
    collected_at = ComplexDateTimeField(required=True)
    name = StringField(max_length=1000, required=True)
    tag = StringField(max_length=1000, required=True)
    type = StringField(max_length=1000)
    valid_since = ComplexDateTimeField()
    valid_until = ComplexDateTimeField()
    values = DictField()
