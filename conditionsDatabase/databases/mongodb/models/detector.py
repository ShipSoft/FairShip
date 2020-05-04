""" Contains a Mongo Engine model definition for a Detector. """
from mongoengine import EmbeddedDocument, EmbeddedDocumentListField, StringField
from condition import Condition


## This model represents a physical device measuring or detecting a certain
#  physical quantity or quantities. A detector may contain other detectors
#  which are then called subdetectors. A detector is associated with zero
#  or more Conditions.
#
#  @property name:            (string) Name of the detector, must not be empty
#                             and must be unique with respect to the parent's namespace.
#  @property conditions:      List of associated Condition models.
#  @property subdetectors:    List of associated Detector models.
class Detector(EmbeddedDocument):
    name = StringField(max_length=1000, required=True)
    conditions = EmbeddedDocumentListField(Condition)
    subdetectors = EmbeddedDocumentListField('self')
