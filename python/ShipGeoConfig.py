import os
import re
import cPickle
import logging


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


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class Config(AttrDict):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self._logger = None

    def set_logger(self, logger):
        self._logger = logger
        return self

    def log(self, s, level=logging.INFO):
        if self._logger is not None:
            self._logger.log(level, s)

    def loads(self, buff):
        rv = cPickle.loads(buff)
        self.clear()
        self.update(rv)
        return self

    def dumps(self):
        return cPickle.dumps(self)

    def load(self, filename):
        with open(expand_env(filename)) as fh:
            self.loads(fh.read())
        return self

    def dump(self, filename):
        with open(expand_env(filename), "w") as fh:
            return fh.write(self.dumps())

    def loadpy(self, filename):
        with open(expand_env(filename)) as fh:
            self.loadpys(fh.read())
        return self

    def loadpys(self, config_string):
        for s in config_string.splitlines():
            if re.match("\s*#", s) or re.match("^\s*$", s):
                continue
            # TODO add parse for "import ROOT as r" or "from A import b"
            if re.search("import .*", s):
                self.log(s, logging.DEBUG)
                exec(s)
                continue
            m = re.search("^\s*([^\s]+)\s*=\s*(.*)", s)
            if m is None or len(m.groups()) != 2:
                self.log("skipping line: " + s, logging.DEBUG)
                pass
            else:
                if m.groups()[0].startswith('self'):
                    self.log(s, logging.DEBUG)
                    exec(s)  # TODO: add some input verification
                else:
                    self.log("'%s' = %s" % m.groups(), logging.DEBUG)
                    self.__setitem__(m.groups()[0], eval(m.groups()[1]))
        return self

    def __str__(self):
        return "ShipGeoConfig:\n  " + "\n  ".join(["%s: %s" % (k, self[k].__str__()) for k in sorted(self.keys()) if not k.startswith("_")])
