# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Typed dataclass definitions for SHiP geometry configuration.

Replaces the dynamic AttrDict-based configuration with statically-typed
dataclasses, enabling mypy/pyrefly verification of all field access.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import typing
from dataclasses import dataclass, field
from typing import Any, Self, Union


class ConfigMixin:
    """Mixin providing dict-like access and serialisation for config dataclasses.

    Enables backward-compatible patterns:
    - ``ship_geo['Bfield']`` (dict-style access)
    - ``for x in ship_geo`` (iteration over field names)
    - ``ship_geo.dumps_json()`` (JSON serialisation)
    - ``ShipGeoConfig.from_dict(d)`` (typed deserialisation)
    """

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        object.__setattr__(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def __iter__(self):
        return iter(f.name for f in dataclasses.fields(self))  # type: ignore[arg-type]

    def keys(self):
        return [f.name for f in dataclasses.fields(self)]  # type: ignore[arg-type]

    def items(self):
        return [(f.name, getattr(self, f.name)) for f in dataclasses.fields(self)]  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)  # type: ignore[call-overload]

    def dumps_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def clone(self):
        return copy.deepcopy(self)

    def __str__(self) -> str:
        name = type(self).__name__
        lines = []
        for f in dataclasses.fields(self):  # type: ignore[arg-type]
            val = getattr(self, f.name)
            if not f.name.startswith("_"):
                lines.append(f"  {f.name}: {val}")
        return f"{name}:\n" + "\n".join(sorted(lines))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        """Recursively construct a typed config from a plain dict.

        Unknown keys are silently ignored (for forward compatibility).
        Missing keys use the dataclass default values.
        """
        if not isinstance(d, dict):
            return d

        hints = typing.get_type_hints(cls)
        field_names = {f.name for f in dataclasses.fields(cls)}  # type: ignore[arg-type]
        kwargs: dict[str, Any] = {}

        for key, value in d.items():
            if key not in field_names:
                continue
            hint = hints.get(key)
            resolved = _resolve_type(hint, value)
            kwargs[key] = resolved

        return cls(**kwargs)


def _resolve_type(hint: Any, value: Any) -> Any:
    """Resolve a value to its expected type, recursively constructing dataclasses."""
    if value is None:
        return None

    origin = typing.get_origin(hint)

    # Handle Optional[X] which is Union[X, None]
    if origin is Union:
        args = typing.get_args(hint)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _resolve_type(non_none[0], value)
        return value

    # If hint is a dataclass with ConfigMixin, recursively construct
    if isinstance(hint, type) and issubclass(hint, ConfigMixin) and isinstance(value, dict):
        return hint.from_dict(value)

    return value


# ---------------------------------------------------------------------------
# Sub-config dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CaveConfig(ConfigMixin):
    """Cave geometry parameters."""

    floorHeightMuonShield: float = 0.0
    floorHeightTankA: float = 0.0
    floorHeightTankB: float = 0.0


@dataclass
class TargetConfig(ConfigMixin):
    """Target station parameters (partially loaded from YAML)."""

    # From YAML
    Nplates: int = 0
    M: list[str] = field(default_factory=list)
    L: list[float] = field(default_factory=list)
    G: list[float] = field(default_factory=list)
    N: list[int] = field(default_factory=list)
    nS: int = 0
    xy: float = 0.0
    HeT: int = 0
    # Computed
    slices_length: list[float] = field(default_factory=list)
    slices_gap: list[float] = field(default_factory=list)
    slices_material: list[str] = field(default_factory=list)
    length: float = 0.0
    z0: float = 0.0
    z: float = 0.0


@dataclass
class HadronAbsorberConfig(ConfigMixin):
    """Hadron absorber parameters."""

    z: float = 0.0
    WithConstField: bool = False


@dataclass
class MuShieldConfig(ConfigMixin):
    """Muon shield parameters."""

    z: float = 0.0
    params: list[float] = field(default_factory=list)
    length: float = 0.0
    nMagnets: int = 0
    Zgap: list[float] = field(default_factory=list)
    half_length: list[float] = field(default_factory=list)
    Entrance: list[float] = field(default_factory=list)
    WithConstField: bool = False


@dataclass
class DecayVolumeConfig(ConfigMixin):
    """Decay volume parameters."""

    length: float = 0.0
    z: float = 0.0
    z0: float = 0.0


@dataclass
class ChambersConfig(ConfigMixin):
    """Vacuum chamber parameters."""

    Tub1length: float = 0.0
    Tub2length: float = 0.0
    Tub3length: float = 0.0
    Tub4length: float = 0.0
    Tub5length: float = 0.0
    Tub6length: float = 0.0
    Rmin: float = 0.0
    Rmax: float = 0.0


@dataclass
class ZPositionConfig(ConfigMixin):
    """Simple config holding a z position (used for TrackStations, Chambers, MuonStations, MuonFilters)."""

    z: float = 0.0


@dataclass
class BfieldConfig(ConfigMixin):
    """Spectrometer magnetic field parameters."""

    z: float = 0.0
    max: float = 0.0
    y: float = 0.0
    x: float = 0.0
    fieldMap: str = ""
    YokeWidth: float = 0.0
    YokeDepth: float = 0.0
    CoilThick: float = 0.0


@dataclass
class TimeDetConfig(ConfigMixin):
    """Timing detector parameters."""

    dzBarRow: float = 0.0
    dzBarCol: float = 0.0
    zBar: float = 0.0
    DZ: float = 0.0
    DX: float = 0.0
    DY: float = 0.0
    z: float = 0.0


@dataclass
class SplitCalConfig(ConfigMixin):
    """Split calorimeter parameters."""

    ZStart: float = 0.0
    XMax: float = 0.0
    YMax: float = 0.0
    Empty: float = 0.0
    BigGap: float = 0.0
    ActiveECALThickness: float = 0.0
    FilterECALThickness: float = 0.0
    FilterECALThickness_first: float = 0.0
    ActiveHCALThickness: float = 0.0
    FilterHCALThickness: float = 0.0
    nECALSamplings: int = 0
    nHCALSamplings: int = 0
    ActiveHCAL: int = 0
    FilterECALMaterial: int = 0
    FilterHCALMaterial: int = 0
    ActiveECALMaterial: int = 0
    ActiveHCALMaterial: int = 0
    ActiveECAL_gas_Thickness: float = 0.0
    num_precision_layers: int = 0
    first_precision_layer: int = 0
    second_precision_layer: int = 0
    third_precision_layer: int = 0
    ActiveECAL_gas_gap: float = 0.0
    NModulesInX: int = 0
    NModulesInY: int = 0
    NStripsPerModule: int = 0
    StripHalfWidth: float = 0.0
    StripHalfLength: float = 0.0
    SplitCalThickness: float = 0.0


@dataclass
class MuonConfig(ConfigMixin):
    """Muon detector parameters."""

    XMax: float = 0.0
    YMax: float = 0.0
    ActiveThickness: float = 0.0
    FilterThickness: float = 0.0


@dataclass
class UpstreamTaggerConfig(ConfigMixin):
    """Upstream tagger parameters."""

    BoxX: float = 0.0
    BoxY: float = 0.0
    BoxZ: float = 0.0
    Z_Position: float = 0.0
    PositionResolution: float = 0.0
    TimeResolution: float = 0.0


@dataclass
class TauMudetConfig(ConfigMixin):
    """Tau/muon detector parameters."""

    Ztot: float = 0.0
    zMudetC: float = 0.0


@dataclass
class StrawtubesDigiConfig(ConfigMixin):
    """Straw tubes digitisation parameters."""

    v_drift: float = 0.0
    sigma_spatial: float = 0.0


@dataclass
class MTCConfig(ConfigMixin):
    """MTC detector parameters (loaded from YAML)."""

    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0
    ironThick: float = 0.0
    sciFiThick: float = 0.0
    num_of_agg_channels: int = 0
    scintThick: float = 0.0
    nLayers: int = 0
    zPosition: Any = "auto"
    fieldY: float = 0.0


@dataclass
class SiliconTargetConfig(ConfigMixin):
    """Silicon target parameters (loaded from YAML)."""

    targetWidth: float = 0.0
    targetHeight: float = 0.0
    sensorWidth: float = 0.0
    sensorLength: float = 0.0
    nLayers: int = 0
    zPosition: Any = "auto"
    targetThickness: float = 0.0
    targetSpacing: float = 0.0
    moduleOffset: float = 0.0


@dataclass
class StrawtubesGeoConfig(ConfigMixin):
    """Straw tubes geometry parameters (loaded from YAML)."""

    width: float = 0.0
    height: float = 0.0
    wire_thickness: float = 0.0
    wall_thickness: float = 0.0
    outer_straw_diameter: float = 0.0
    straw_pitch: float = 0.0
    y_layer_offset: float = 0.0
    delta_z_layer: float = 0.0
    delta_z_view: float = 0.0
    view_angle: float = 0.0
    station_width: float = 0.0
    station_height: float = 0.0
    station_length: float = 0.0
    # Set dynamically in shipDet_conf.py
    medium: str = ""
    frame_material: str = ""


@dataclass
class ShipGeoConfig(ConfigMixin):
    """Top-level SHiP geometry configuration.

    All fields match the attributes set in geometry_config.create_config().
    """

    # Scalar parameters
    DecayVolumeMedium: str = "helium"
    SND: bool = True
    SND_design: list[int] = field(default_factory=lambda: [2])
    target_yaml: str = ""
    shieldName: str = ""
    SC_mag: bool = False
    Yheight: float = 0.0
    strawDesign: int = 10
    magnetDesign: int = 4
    z: float = 0.0
    xMax: float = 0.0
    HcalOption: int = -1
    EcalOption: int = 2
    muShieldGeo: Any = None
    nuTargetPassive: int = 1

    # Nested sub-configs
    cave: CaveConfig = field(default_factory=CaveConfig)
    target: TargetConfig = field(default_factory=TargetConfig)
    hadronAbsorber: HadronAbsorberConfig = field(default_factory=HadronAbsorberConfig)
    muShield: MuShieldConfig = field(default_factory=MuShieldConfig)
    decayVolume: DecayVolumeConfig = field(default_factory=DecayVolumeConfig)
    chambers: ChambersConfig = field(default_factory=ChambersConfig)
    Bfield: BfieldConfig = field(default_factory=BfieldConfig)
    TimeDet: TimeDetConfig = field(default_factory=TimeDetConfig)
    SplitCal: SplitCalConfig = field(default_factory=SplitCalConfig)
    Muon: MuonConfig = field(default_factory=MuonConfig)
    UpstreamTagger: UpstreamTaggerConfig = field(default_factory=UpstreamTaggerConfig)
    tauMudet: TauMudetConfig = field(default_factory=TauMudetConfig)
    strawtubesDigi: StrawtubesDigiConfig = field(default_factory=StrawtubesDigiConfig)

    # ZPosition-based sub-configs
    TrackStation1: ZPositionConfig = field(default_factory=ZPositionConfig)
    TrackStation2: ZPositionConfig = field(default_factory=ZPositionConfig)
    TrackStation3: ZPositionConfig = field(default_factory=ZPositionConfig)
    TrackStation4: ZPositionConfig = field(default_factory=ZPositionConfig)
    Chamber1: ZPositionConfig = field(default_factory=ZPositionConfig)
    Chamber6: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonStation0: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonStation1: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonStation2: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonStation3: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonFilter0: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonFilter1: ZPositionConfig = field(default_factory=ZPositionConfig)
    MuonFilter2: ZPositionConfig = field(default_factory=ZPositionConfig)

    # Optional YAML-sourced configs (set in shipDet_conf.py)
    mtc_geo: MTCConfig | None = None
    SiliconTarget_geo: SiliconTargetConfig | None = None
    strawtubes_geo: StrawtubesGeoConfig | None = None

    # Metadata (set by saveBasicParameters.py)
    FairShip: Any = None
    FairRoot: Any = None
