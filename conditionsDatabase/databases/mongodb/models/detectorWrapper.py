""" Contains a Mongo Engine model definition for a Detector Wrapper. """
from mongoengine import Document, EmbeddedDocumentField, StringField
from detector import Detector


## An object that wraps a Detector model and everything that it contains.
#  Mongo Engine saves collections of Documents, however, you don't have the option
#  to include a Document within a Document. They provide a specific type for that
#  (EmbeddedDocument). As a result, the Detector model, that can be nested inside
#  itself, could not inherit from the class Document. The solution to that is
#  to create an extra layer, which inherits from Document, and wraps the
#  Detector. Users have no knowledge of this extra layer.
#
#  @property name:        (string) The same name as the name of the dectector it
#                         contains; must not be empty and must be unique.
#  @property detector:    The actual detector model that is being wrapped. There is
#                         always exactly one detector inside a wrapper.
class DetectorWrapper(Document):
    name = StringField(max_length=1000, primary_key=True, required=True)
    detector = EmbeddedDocumentField(Detector)
