"""
Module with global variables reused across the project.

An antipattern, but useful to set quick changes here and there.
Should be swapped out for a proper settings structure, for example
pydantic: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

debug = False
h = dict()
modules = dict()
ShipGeo = None
EcalDebugDraw = None
ecalGeoFile = None
fieldMaker = None
pidProton = None
realPR = None
vertexing = None
withNoStrawSmearing = None
withT0 = None
