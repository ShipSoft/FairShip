from typing import Any

class SeedingAlgorithm:
    TruthSmeared: Any
    TruthEstimated: Any
    Default: Any
    Orthogonal: Any

class TrackSmearingSigmas:
    def __init__(self, **kwargs: Any) -> None: ...

class VertexFinder:
    Truth: Any
    AMVF: Any
    Iterative: Any

def addKalmanTracks(*args: Any, **kwargs: Any) -> None: ...
def addSeeding(*args: Any, **kwargs: Any) -> None: ...
def addVertexFitting(*args: Any, **kwargs: Any) -> None: ...
