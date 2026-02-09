# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os
from argparse import ArgumentParser

import geometry_config
import geomGeant4
import ROOT as r
import ShieldUtils
import shipDet_conf
import shipunit as u


def create_csv_field_map(options):
    r.gErrorIgnoreLevel = r.kWarning
    r.gSystem.Load("libpythia8")

    ship_geo = geometry_config.create_config(
        Yheight=10.0, strawDesign=10, muShieldGeo=options.geofile, shieldName=getattr(options, "shieldName", "warm_opt")
    )

    ship_geo.muShield.WithConstField = True

    run = r.FairRunSim()
    run.SetName("TGeant4")  # Transport engine
    run.SetSink(r.FairRootFileSink("tmp_file"))  # Output file
    # user configuration file default g4Config.C
    run.SetUserConfig("g4Config.C")
    shipDet_conf.configure(run, ship_geo)
    primGen = r.FairPrimaryGenerator()
    primGen.SetTarget(ship_geo.target.z0 + 70.845 * u.m, 0.0)
    #
    run.SetGenerator(primGen)
    run.SetStoreTraj(r.kFALSE)
    run.Init()
    fieldMaker = geomGeant4.addVMCFields(ship_geo, "", True)

    field_center, shield_half_length = ShieldUtils.find_shield_center(ship_geo)
    print(
        "SHIELD ONLY: CENTER: {}, HALFLENGTH: {}, half_X: {}, half_Y: {}".format(
            field_center, shield_half_length, ship_geo.muShield.half_X_max, ship_geo.muShield.half_Y_max
        )
    )
    fieldMaker.generateFieldMap(
        os.path.expandvars("$FAIRSHIP/files/fieldMap.csv"),
        2.5,
        ship_geo.muShield.half_X_max,
        ship_geo.muShield.half_Y_max,
        shield_half_length,
        field_center,
    )


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--muShieldDesign", dest="ds", required=True, type=int)
    parser.add_argument(
        "--stepMuonShield",
        dest="muShieldStepGeo",
        help="activate steps geometry for the muon shield",
        required=False,
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--coMuonShield",
        dest="muShieldWithCobaltMagnet",
        help="""replace one of the magnets in the shield with 2.2T cobalt one,
                             downscales other fields, works only for muShieldDesign >2""",
        required=False,
        type=int,
        default=0,
    )
    parser.add_argument(
        "-g", dest="geofile", help="geofile for muon shield geometry, for experts only", required=False, default=None
    )
    options = parser.parse_args()
    create_csv_field_map(options)
