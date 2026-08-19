from typing import Any

from acts import logging as logging

class Vector3:
    def __init__(self, x: float, y: float, z: float) -> None: ...

class ConstantBField:
    def __init__(self, field: Vector3) -> None: ...

class UnitConstants:
    GeV: float
    T: float
    mm: float
    ns: float
    cm: float
    degree: float

class ParticleHypothesis:
    muon: ParticleHypothesis

class TrackSelector:
    class Config:
        def __init__(self, *, minMeasurements: int = ..., **kwargs: Any) -> None: ...

class GeometryIdentifier:
    def __init__(self, *, volume: int = ..., layer: int = ..., sensitive: int = ...) -> None: ...
    value: int

class Barcode:
    def __init__(
        self,
        *,
        primaryVertex: int = ...,
        secondaryVertex: int = ...,
        part: int = ...,
        gen: int = ...,
        subpart: int = ...,
    ) -> None: ...
    value: int

class GeometryContext:
    def __init__(self) -> None: ...

def createShipFieldProvider(field_map_path: str, unit: float) -> Any: ...
def pushRecoVertex(vector_ptr: int, vertex: Any, tracks: Any, input_addr: int) -> None: ...
def get_last_extracted_params_addr() -> int: ...
