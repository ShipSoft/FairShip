# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import json
import os
import pickle


class AttrDict(dict):
    """
    dict class that can address its keys as fields, e.g.
    d['key'] = 1
    assert d.key == 1
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def clone(self):
        result = AttrDict()
        for k, v in self.items():
            if isinstance(v, AttrDict):
                result[k] = v.clone()
            else:
                result[k] = v
        return result


class Config(AttrDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def loads(self, buff):
        rv = pickle.loads(buff)
        self.clear()
        self.update(rv)
        return self

    def loads_json(self, json_str):
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

    def clone(self):
        result = Config()
        for k, v in self.items():
            if isinstance(v, AttrDict):
                result[k] = v.clone()
            else:
                result[k] = v
        return result

    def dumps(self):
        return pickle.dumps(self)

    def dumps_json(self):
        """Serialize config to JSON string"""
        return json.dumps(self, indent=2, default=str)

    def load(self, filename):
        with open(os.path.expandvars(filename)) as fh:
            self.loads(fh.read())
        return self

    def dump(self, filename):
        with open(os.path.expandvars(filename), "w") as fh:
            return fh.write(self.dumps())

    def __str__(self):
        return "ShipGeoConfig:\n  " + "\n  ".join(
            [f"{k}: {self[k].__str__()}" for k in sorted(self.keys()) if not k.startswith("_")]
        )


def load_from_root_file(root_file, key="ShipGeo"):
    """
    Load configuration from ROOT file.

    Automatically detects and handles both formats:
    - New format: JSON string (stored as std::string or TObjString)
    - Old format: Pickled Python object

    Args:
        root_file: Either a ROOT.TFile object or a string path to ROOT file
        key: The key name for the stored config (default: 'ShipGeo')

    Returns:
        Config object with the loaded configuration
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
            # JSON format - parse it
            config = Config()
            config.loads_json(content_str)
        else:
            # Assume pickle format - unpickle it
            # Convert to bytes for pickle (using latin-1 encoding)
            pickle_bytes = content_str.encode("latin-1")
            config = pickle.loads(pickle_bytes)

            # Ensure it's a Config object (might be if it was pickled as Config)
            if not isinstance(config, Config):
                # Wrap in Config if needed
                c = Config()
                c.update(config)
                config = c

        return config

    finally:
        if own_file:
            root_file.Close()
