# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from __future__ import annotations

import json
import os
import pickle

from ship_geo_config_types import ShipGeoConfig  # noqa: F401 — re-export


class AttrDict(dict):
    """
    dict class that can address its keys as fields, e.g.
    d['key'] = 1
    assert d.key == 1
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def clone(self) -> AttrDict:
        result = AttrDict()
        for k, v in self.items():
            if isinstance(v, AttrDict):
                result[k] = v.clone()
            else:
                result[k] = v
        return result


class Config(AttrDict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def loads(self, buff: bytes):
        rv = pickle.loads(buff)
        self.clear()
        self.update(rv)
        return self

    def loads_json(self, json_str: str):
        """Deserialize config from JSON string"""

        def dict_to_attrdict(d):
            """Recursively convert dict to AttrDict"""
            if isinstance(d, dict):
                result = AttrDict()
                for k, v in d.items():
                    result[k] = dict_to_attrdict(v)
                return result
            elif isinstance(d, list):
                return [dict_to_attrdict(item) for item in d]
            else:
                return d

        rv = json.loads(json_str)
        self.clear()
        # Convert nested dicts to AttrDict
        for k, v in rv.items():
            self[k] = dict_to_attrdict(v)
        return self

    def clone(self) -> Config:
        result = Config()
        for k, v in self.items():
            if isinstance(v, AttrDict):
                result[k] = v.clone()
            else:
                result[k] = v
        return result

    def dumps(self) -> bytes:
        return pickle.dumps(self)

    def dumps_json(self) -> str:
        """Serialize config to JSON string"""
        return json.dumps(self, indent=2, default=str)

    def load(self, filename):
        with open(os.path.expandvars(filename), "rb") as fh:
            self.loads(fh.read())
        return self

    def dump(self, filename) -> int:
        with open(os.path.expandvars(filename), "wb") as fh:
            return fh.write(self.dumps())

    def __str__(self) -> str:
        return "ShipGeoConfig:\n  " + "\n  ".join(
            [f"{k}: {self[k].__str__()}" for k in sorted(self.keys()) if not k.startswith("_")]
        )


def _config_to_dict(config: Config) -> dict:
    """Convert a legacy Config/AttrDict to a plain dict (recursively)."""
    result = {}
    for k, v in config.items():
        if isinstance(v, dict):
            result[k] = _config_to_dict(v)  # type: ignore[arg-type]
        else:
            result[k] = v
    return result


def load_from_root_file(root_file, key: str = "ShipGeo") -> ShipGeoConfig:
    """
    Load configuration from ROOT file.

    Automatically detects and handles both formats:
    - New format: JSON string (stored as std::string or TObjString)
    - Old format: Pickled Python object

    Args:
        root_file: Either a ROOT.TFile object or a string path to ROOT file
        key: The key name for the stored config (default: 'ShipGeo')

    Returns:
        ShipGeoConfig object with the loaded configuration
    """
    import ROOT

    own_file = False
    if isinstance(root_file, str):
        root_file = ROOT.TFile.Open(root_file)
        own_file = True

    try:
        # Get the object (could be std::string or TObjString)
        config_obj = root_file.Get(key)
        if not config_obj:
            raise ValueError(f"No object with key '{key}' found in ROOT file")

        # Convert to Python string
        content_str = str(config_obj)

        # Auto-detect format by checking first character
        if content_str.startswith("{"):
            # JSON format — parse to typed config
            d = json.loads(content_str)
            return ShipGeoConfig.from_dict(d)
        else:
            # Pickle format (legacy) — unpickle, convert to typed config
            pickle_bytes = content_str.encode("latin-1")
            legacy = pickle.loads(pickle_bytes)

            if isinstance(legacy, dict):
                return ShipGeoConfig.from_dict(_config_to_dict(legacy))  # type: ignore[arg-type]
            else:
                # Unexpected type, wrap as best we can
                c = Config()
                c.update(legacy)
                return ShipGeoConfig.from_dict(_config_to_dict(c))

    finally:
        if own_file:
            root_file.Close()
