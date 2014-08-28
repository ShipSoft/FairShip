#!/usr/bin/env python
import unittest
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry


class TestSingleConfig(unittest.TestCase):
    def setUp(self):
        self.key = "bb"
        with ConfigRegistry.register_config("bb") as c:
            c.length = 10
            c.width = 20

    def test_len(self):
        assert len(ConfigRegistry.keys()) == 1, ConfigRegistry.keys()

    def test_key(self):
        assert self.key in ConfigRegistry.keys()

    def test_value(self):
        assert ConfigRegistry[self.key].length == 10

    def tearDown(self):
        ConfigRegistry.clean()


class TestInheritance(unittest.TestCase):
    def setUp(self):
        with ConfigRegistry.register_config("bb") as c:
            c.length = 10
            c.width = 20
            c.muShield = AttrDict(z=10) 
        with ConfigRegistry.register_config("cc", base="bb") as c:
            c.height = 30
            c.volume = c.length * c.height * c.width

    def test_len(self):
        assert len(ConfigRegistry.keys()) == 2

    def test_key(self):
        assert "bb" in ConfigRegistry.keys()
        assert "cc" in ConfigRegistry.keys()

    def test_value(self):
        assert ConfigRegistry["bb"].length == 10
        assert ConfigRegistry["cc"].length == 10
        assert ConfigRegistry["cc"].muShield.z == 10
        assert ConfigRegistry["bb"].muShield.z == 10

    def test_latest(self):
        c = ConfigRegistry.get_latest_config()
        self.assertIsNotNone(c)
        self.assertEqual(c.height, 30)

    def tearDown(self):
        ConfigRegistry.clean()


class TestStringSingleConfig(unittest.TestCase):
    def setUp(self):
        self.key = "basic"
        config = """
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry

with ConfigRegistry.register_config("basic") as c:
    c.vetoStation = AttrDict(z=-2390.*u.cm)
    c.TrackStation1 = AttrDict(z=1510.*u.cm)
    c.TrackStation2 = AttrDict(z=1710.*u.cm)
    c.TrackStation3 = AttrDict(z=2150.*u.cm)
    c.TrackStation4 = AttrDict(z=2370.*u.cm)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI

    # target absorber muon shield setup
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    c.muShield               =  AttrDict(z=0*u.cm)
    c.muShield.dZ1 = 2.5*u.m
    c.muShield.dZ2 = 3.5*u.m
    c.muShield.dZ3 = 3.0*u.m
    c.muShield.dZ4 = 3.0*u.m
    c.muShield.dZ5 = 2.5*u.m
    c.muShield.dZ6 = 2.5*u.m
    c.muShield.LE  = 5*u.m
        """
        ConfigRegistry.loadpys(config)

    def test_len(self):
        assert len(ConfigRegistry.keys()) == 1, ConfigRegistry.keys()

    def test_key(self):
        assert self.key in ConfigRegistry.keys()

    def test_value(self):
        assert ConfigRegistry[self.key].Bfield.max  == 1.5*u.kilogauss

    def tearDown(self):
        ConfigRegistry.clean()


class TestStringConditionalConfig(unittest.TestCase):
    def setUp(self):
        self.key = "basic"
        self.config = """
import shipunit as u
from ShipGeoConfig import AttrDict, ConfigRegistry

with ConfigRegistry.register_config("basic") as c:
    c.vetoStation = AttrDict(z=-2390.*u.cm)
    c.TrackStation1 = AttrDict(z=1510.*u.cm)
    c.TrackStation2 = AttrDict(z=1710.*u.cm)
    c.TrackStation3 = AttrDict(z=2150.*u.cm)
    c.TrackStation4 = AttrDict(z=2370.*u.cm)

    c.z = c.TrackStation2.z + 0.5 * (c.TrackStation3.z - c.TrackStation2.z)

    c.Bfield = AttrDict(z=c.z)
    c.Bfield.max = 1.5*u.kilogauss  # was 1.15 in EOI

    # target absorber muon shield setup
    c.decayVolume            =  AttrDict(z=0*u.cm)
    c.decayVolume.length     =   50*u.m

    if MU_SHIELD_ENABLED:
        c.muShield               =  AttrDict(z=0*u.cm)
        c.muShield.dZ1 = 2.5*u.m
        c.muShield.dZ2 = 3.5*u.m
        c.muShield.dZ3 = 3.0*u.m
        c.muShield.dZ4 = 3.0*u.m
        c.muShield.dZ5 = 2.5*u.m
        c.muShield.dZ6 = 2.5*u.m
        c.muShield.LE  = 5*u.m
        """

    def test_true(self):
        c = ConfigRegistry.loadpys(self.config, MU_SHIELD_ENABLED=True)
        self.assertIn("muShield", c)
        assert len(ConfigRegistry.keys()) == 1, ConfigRegistry.keys()
        assert self.key in ConfigRegistry.keys()
        assert ConfigRegistry[self.key].Bfield.max  == 1.5*u.kilogauss
        assert ConfigRegistry[self.key].muShield.dZ1 == 2.5*u.m

    def test_false(self):
        ConfigRegistry.loadpys(self.config, MU_SHIELD_ENABLED=False)
        assert len(ConfigRegistry.keys()) == 1, ConfigRegistry.keys()
        assert self.key in ConfigRegistry.keys()
        assert ConfigRegistry[self.key].Bfield.max  == 1.5*u.kilogauss
        self.assertNotIn("muShield", ConfigRegistry[self.key])

    def tearDown(self):
        ConfigRegistry.clean()


if __name__ == '__main__':
    unittest.main()
