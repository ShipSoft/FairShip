from future import standard_library
standard_library.install_aliases()
import os
import re
import pickle
from contextlib import contextmanager
from future.utils import with_metaclass


def expand_env(string):
    """
    Expand environment variables in string:
    $HOME/bin -> /home/user/bin
    """
    while True:
        m = re.search("(\${*(\w+)}*)", string)
        if m is None:
            break
        (env_token, env_name) = m.groups()
        assert env_name in os.environ, "Environment variable '%s' is not defined" % env_name
        env_value = os.environ[env_name]
        string = string.replace(env_token, env_value)
    return string


class _SingletonDict(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_SingletonDict, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def __getitem__(cls, key):
        return cls._instances[cls][key]

    def delitem(cls, key):
        del(cls._instances[cls][key])


class ConfigRegistry(with_metaclass(_SingletonDict, dict)):
    """
    Singleton registry of all Configurations
    """
    recent_config_name = None

    @staticmethod
    def loadpy(filename, **kwargs):
        with open(expand_env(filename)) as fh:
            return ConfigRegistry.loadpys(fh.read(), **kwargs)

    @staticmethod
    def loadpys(config_string, **kwargs):
        string_unixlf = config_string.replace('\r', '')
        exec(string_unixlf, kwargs)
        return ConfigRegistry.get_latest_config()

    @staticmethod
    def get_latest_config():
        return ConfigRegistry[ConfigRegistry.recent_config_name]

    def __init__(self):
        self.__dict__ = self

    @staticmethod
    @contextmanager
    def register_config(name=None, base=None):
        registry = ConfigRegistry()
        if base is not None:
            assert base in registry, "no base configuration (%s) found in the registry" % base
            config = registry[base].clone()
        else:
            config = Config()
        yield config
        if name is not None:
            registry[name] = config
            ConfigRegistry.recent_config_name = name

    @staticmethod
    def keys():
        registry = ConfigRegistry()
        return [k for k, v in registry.items()]

    @staticmethod
    def get(name):
        return ConfigRegistry[name]

    @staticmethod
    def clean():
        for k in ConfigRegistry.keys():
            ConfigRegistry.delitem(k)


class AttrDict(dict):
    """ 
    dict class that can address its keys as fields, e.g.
    d['key'] = 1
    assert d.key == 1
    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
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
        super(Config, self).__init__(*args, **kwargs)

    def loads(self, buff):
        rv = pickle.loads(buff)
        self.clear()
        self.update(rv)
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

    def load(self, filename):
        with open(expand_env(filename)) as fh:
            self.loads(fh.read())
        return self

    def dump(self, filename):
        with open(expand_env(filename), "w") as fh:
            return fh.write(self.dumps())

    def __str__(self):
        return "ShipGeoConfig:\n  " + "\n  ".join(["%s: %s" % (k, self[k].__str__()) for k in sorted(self.keys()) if not k.startswith("_")])
