from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentListField, StringField


class Parameter(EmbeddedDocument):
    name = StringField(max_length=100, null=True)
    value = StringField(max_length=100, null=True)


class Subdetector (Document):
    name = StringField(max_length=100, null=True)
    parameters = EmbeddedDocumentListField(Parameter)
