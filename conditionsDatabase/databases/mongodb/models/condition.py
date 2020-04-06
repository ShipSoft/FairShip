"""Contains a Mongo Engine model definition for a Condition."""
from mongoengine import EmbeddedDocument, DynamicField, StringField, ComplexDateTimeField


## This model represents meta-data about an experiment describing a specific (set of)
#  value(s) (i.e. a condition under which an experiment took place) at a date/time
#  when the condition was measured/collected. Conditions are associated with a Detector.
#
#  @param collected_at:    (datetime) The date/time that the condition was collected;
#                          must not be empty.
#  @param name:            (string) Name of the condition; must not be empty.
#  @param tag:             (string) Tag for the condition; must not be empty.
#  @param type:            (string) Type of the condition.
#  @param valid_since:     (datetime) The date/time defining the values' validity start.
#  @param valid_until:     (datetime) The date/time defining the values' validity end.
#  @param values:          (mixed) Values for / describing the condition.
class Condition(EmbeddedDocument):
    collected_at = ComplexDateTimeField(required=True)
    name = StringField(max_length=1000, required=True)
    tag = StringField(max_length=1000, required=True)
    type = StringField(max_length=1000)
    valid_since = ComplexDateTimeField()
    valid_until = ComplexDateTimeField()
    values = DynamicField()
