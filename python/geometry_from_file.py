# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Simulate on the geometry of a geometry file (run_simScript.py -g).

The modules build their geometry as usual, from the configuration (ShipGeo)
stored in the geometry file. Building does more than create volumes: the
detectors register which volumes are sensitive, and magnets attach their
fields to volumes, and a geometry file keeps neither. So the run keeps all of
that and only exchanges the volumes: a GeometrySwap module (make_swap), added last,
replaces the geometry that was just built by the one stored in the file, before
Geant4 converts it. Particles are then transported through the stored geometry,
whatever the current code would build.

For this to be safe, every volume and placement the current code builds must
exist in the stored geometry (sensitive volumes are found by name, detector
IDs come from node names and copy numbers), and the fields attached to volumes
are copied onto the stored volumes. Fields from field maps
are added after the swap, as usual.
"""

from __future__ import annotations

from typing import Any

import ROOT

_HELPER = """
#include <string>
#include <unordered_set>
#include <vector>

#include "TGeoManager.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"

namespace ship_geofile {
// Read the stored geometry without making it the current one. Reading a
// TGeoManager deletes gGeoManager, but the geometry that was built must stay
// alive: FairMCApplication still uses its list of volumes, and its fields are
// copied. FairModule::ConstructRootGeometry() does the same.
inline TGeoManager* Import(const char* path) {
  TGeoManager* built = gGeoManager;
  gGeoManager = nullptr;
  TGeoManager* loaded = TGeoManager::Import(path, "FAIRGeom");
  gGeoManager = built;
  return loaded;
}

inline void Use(TGeoManager* geometry) { gGeoManager = geometry; }

// Names of the volumes and of their placements ("volume/node").
inline std::unordered_set<std::string> Placements(TGeoManager* geometry) {
  std::unordered_set<std::string> names;
  TIter next(geometry->GetListOfVolumes());
  while (auto* volume = static_cast<TGeoVolume*>(next())) {
    names.insert(volume->GetName());
    for (Int_t i = 0; i < volume->GetNdaughters(); ++i) {
      names.insert(std::string(volume->GetName()) + "/" + volume->GetNode(i)->GetName());
    }
  }
  return names;
}

// Volumes and placements of `built` that `loaded` lacks.
inline std::vector<std::string> Missing(TGeoManager* built, TGeoManager* loaded) {
  const auto have = Placements(loaded);
  std::vector<std::string> missing;
  for (const auto& name : Placements(built)) {
    if (!have.count(name)) missing.push_back(name);
  }
  return missing;
}
}  // namespace ship_geofile
"""


def check_file(geofile: str) -> None:
    """Raise ValueError unless geofile holds a geometry (FAIRGeom) and its configuration (ShipGeo)."""
    try:
        f = ROOT.TFile.Open(geofile, "READ")
    except OSError:  # recent PyROOT raises instead of returning a null file
        f = None
    if not f or f.IsZombie():
        raise ValueError(f"cannot open geometry file {geofile}")
    with f:
        key = f.GetKey("FAIRGeom")
        has_geometry = bool(key) and key.GetClassName() == "TGeoManager"
        has_config = bool(f.GetKey("ShipGeo"))
    if not has_geometry:
        raise ValueError(f"{geofile} has no geometry FAIRGeom: give a geometry file written by run_simScript.py")
    if not has_config:
        raise ValueError(
            f"{geofile} has no geometry configuration ShipGeo: give a geometry file written by run_simScript.py"
        )


SWAP_NAME = "GeometrySwap"
_swap_class: Any = None


def make_swap(geofile: str) -> Any:
    """The module that replaces the built geometry by the one in geofile; add it last.

    The class derives from pyFairModule, so it is defined on first use only:
    this keeps the library of pyFairModule from being loaded whenever this
    module is imported, as it is by shipDet_conf.
    """
    global _swap_class
    if _swap_class is None:
        _swap_class = _define_swap_class()
    return _swap_class(geofile)


def _define_swap_class() -> Any:
    class GeometrySwap(ROOT.pyFairModule):
        """Module that replaces the built geometry by the one in a geometry file; add it last."""

        def __init__(self, geofile: str) -> None:
            ROOT.pyFairModule.__init__(self, self)
            self.SetName(SWAP_NAME)
            self.geofile = geofile
            self.loaded: Any = None
            self.fields: list[str] = []
            self.error: str | None = None

        def ConstructGeometry(self) -> None:
            # An exception raised here would pass through the C++ of Geant4 VMC,
            # which calls this method. Record it instead: the built geometry then
            # stays in use, and check_swapped() stops the run after run.Init().
            try:
                self._swap()
            except Exception as e:
                self.error = str(e)
                print(f"ERROR in GeometrySwap: {e}", flush=True)

        def _swap(self) -> None:
            if not hasattr(ROOT, "ship_geofile"):
                ROOT.gInterpreter.Declare(_HELPER)
            helper = ROOT.ship_geofile  # declared above
            built = ROOT.gGeoManager
            loaded = helper.Import(self.geofile)
            if not loaded:
                raise RuntimeError(f"cannot read the geometry FAIRGeom from {self.geofile}")

            # Detectors find their sensitive volumes by name, and compute detector
            # IDs from node names and copy numbers.
            missing = sorted(str(name) for name in helper.Missing(built, loaded))
            if missing:
                raise RuntimeError(
                    f"the geometry in {self.geofile} lacks {len(missing)} volume(s) or placement(s) that the current"
                    f" code builds ({', '.join(missing[:10])}{', ...' if len(missing) > 10 else ''}); detectors"
                    " could record no hits or wrong detector IDs"
                )

            # Fields attached to volumes are not stored in geometry files.
            built_volumes = list(built.GetListOfVolumes())
            loaded_volumes = list(loaded.GetListOfVolumes())
            same_order = [v.GetName() for v in built_volumes] == [v.GetName() for v in loaded_volumes]
            by_name: dict[str, list[Any]] = {}
            for volume in loaded_volumes:
                by_name.setdefault(volume.GetName(), []).append(volume)
            fields = []
            for i, volume in enumerate(built_volumes):
                field = volume.GetField()
                if not field:
                    continue
                if same_order:
                    target = loaded_volumes[i]
                else:
                    candidates = by_name[volume.GetName()]
                    if len(candidates) != 1:
                        raise RuntimeError(
                            f"cannot tell which of the {len(candidates)} volumes {volume.GetName()} in {self.geofile}"
                            " gets the magnetic field of the volume of that name"
                        )
                    target = candidates[0]
                fields.append((target, field, volume.GetName()))
            for target, field, name in fields:
                target.SetField(field)
                self.fields.append(name)

            helper.Use(loaded)
            self.loaded = loaded
            # The parameter file stores the geometry given to FairGeoParSet by FairRunSim::Init().
            geo_par = ROOT.FairRuntimeDb.instance().getContainer("FairGeoParSet")
            if geo_par:
                geo_par.SetGeometry(loaded)
            print(
                f"GeometrySwap: transporting through the geometry of {self.geofile} ({len(loaded_volumes)} volumes);"
                f" magnetic fields of volumes copied for: {', '.join(self.fields) or 'none'}",
                flush=True,
            )

    return GeometrySwap


def check_swapped(swap: Any) -> None:
    """After run.Init(): stop unless the geometry from the file is the one in use."""
    in_use = ROOT.gGeoManager
    if swap.error or not swap.loaded or not in_use or ROOT.addressof(in_use) != ROOT.addressof(swap.loaded):
        reason = swap.error or "GeometrySwap.ConstructGeometry() did not run or did not complete"
        raise RuntimeError(f"the geometry from {swap.geofile} is not in use: {reason}")


# Parts of the geometry configuration that shipDet_conf.configure reads again
# from the YAML files in $FAIRSHIP/geometry, also with -g.
YAML_CONFIGS = {
    "mtc_geo": "MTC_config.yaml",
    "SiliconTarget_geo": "SiliconTarget_config.yaml",
    "strawtubes_geo": "strawtubes_config.yaml",
}


def stored_yaml_configs(ship_geo: Any) -> dict[str, Any]:
    """The parts of the stored configuration that the YAML files will overwrite."""
    return {key: ship_geo[key] for key in YAML_CONFIGS if key in ship_geo}


def check_yaml_configs(stored: dict[str, Any], ship_geo: Any) -> None:
    """Check that the YAML files still give the configuration stored with the geometry.

    The detectors take their parameters from the YAML files, so if these changed
    since the geometry file was written, the parameters would not match the
    stored geometry.
    """
    changed = [YAML_CONFIGS[key] for key, value in stored.items() if dict(ship_geo.get(key, {})) != dict(value)]
    if changed:
        raise ValueError(
            f"geometry/{', geometry/'.join(changed)} changed since the geometry file was written, so the detector"
            " parameters would not match the stored geometry: write a new geometry file"
        )
