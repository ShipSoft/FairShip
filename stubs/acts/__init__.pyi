from collections.abc import Sequence
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
    volume: int
    layer: int
    sensitive: int
    boundary: int
    approach: int
    extra: int

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

class MagneticFieldContext:
    def __init__(self) -> None: ...

class Navigator:
    class Config:
        trackingGeometry: Any
        resolveMaterial: bool
        resolvePassive: bool
        resolveSensitive: bool

    def __init__(self, cfg: Navigator.Config, level: Any = ...) -> None: ...

class EigenStepper:
    def __init__(self, field: Any) -> None: ...

class Propagator:
    def __init__(self, stepper: Any, navigator: Any) -> None: ...

def createShipFieldProvider(field_map_path: str, unit: float) -> Any: ...
def pushRecoVertex(vector_ptr: int, vertex: Any, tracks: Any, input_addr: int) -> None: ...
def get_last_extracted_params_addr() -> int: ...
def createPlaneSurface(center: Any, normal: Any) -> Any: ...
def createTrackParameters(
    x: float,
    y: float,
    z: float,
    px: float,
    py: float,
    pz: float,
    charge: float,
    surface: Any,
    cov: Sequence[float],
    geo_ctx: GeometryContext,
) -> Any: ...
def processMeasurements(hits: Any, trackingGeometry: Any) -> Any: ...
def getMeasurementGeoId(measurements: Any, index: int) -> GeometryIdentifier: ...
def getSurface(trackingGeometry: Any, geo_id: GeometryIdentifier) -> Any: ...
def fitTrack(
    measurements: Any,
    indices: Sequence[int],
    initialParams: Any,
    outputTracks: Any,
    trackingGeometry: Any,
    magneticField: Any,
) -> bool: ...
def fitVertex(proxies: Any, bField: Any, geoCtx: GeometryContext, trackingGeometry: Any) -> list[Any]: ...
def extrapolateTrack(
    propagator: Any,
    start: Any,
    target: Any,
    geoCtx: GeometryContext,
    magCtx: MagneticFieldContext,
) -> Any | None: ...
def extrapolateTrackToZ(track_ptr_addr: int, targetZ_ship: float) -> tuple: ...
