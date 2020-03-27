"""package conditionsDatabase
Contains a Mongo Engine model definition for a Detector
"""
from mongoengine import EmbeddedDocument, EmbeddedDocumentListField, StringField
from condition import Condition

## This model represents a physical device measuring or detecting a certain
#  physical quantity or quantities. A detector may contain other detectors
#  which are then called subdetectors. A detector is associated with zero
#  or more Conditions.
#  @param name: name of detector, should not be empty
#  @param conditions: list of conditions
#  @param subdetectors: list of detectors
class Detector(EmbeddedDocument):
    name = StringField(max_length=1000, required=True)
    conditions = EmbeddedDocumentListField(Condition)
    subdetectors = EmbeddedDocumentListField('self')
