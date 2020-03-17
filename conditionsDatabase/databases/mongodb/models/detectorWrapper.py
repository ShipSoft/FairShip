"""
@package conditionsDatabase
Contains a Mongo Engine model definition for a Detector Wrapper
"""
from mongoengine import Document, EmbeddedDocumentField, StringField
from detector import Detector

class DetectorWrapper(Document):
    """
    Mongo Engine saves collections of Documents, however, you don't have the option
    to include a Document withing a Document. They provide a specific type for that
    (EmbeddedDocument). As a result, the Detector class, which has an attribute of
    arbitrary many Detectors, could not inherit from the class Document. The solution
    to that was to create an extra layer, which inherits from Document, and wraps the
    Detector. Users have no knowledge of this layer.

    :param: name - the same as the first detector name; should not be empty and should be unique
    :param: detector - there is always only 1 detector inside a wrapper
    """
    name = StringField(max_length=1000, primary_key=True, required=True)
    detector = EmbeddedDocumentField(Detector)
