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

The stored geometry may differ from the one the current code builds, for
example a geometry file written with a modified SBT design. What must match is
what the run keeps from building:

* Every volume that the modules register as sensitive must exist in the stored
  geometry: FairDetector::Initialize() binds sensitive volumes to the geometry
  given to Geant4 by name, so a detector would record no hits in a volume the
  stored geometry lacks. The run stops otherwise.
* Every volume to which a field is attached must exist in the stored geometry,
  and its name must tell which one: the field is copied onto it. The run stops
  otherwise. Fields from field maps are added after the swap, as usual.

Other differences only change the material that particles go through, which
is the point of simulating on a stored geometry, and are reported as a
warning: passive volumes that the stored geometry lacks, placements that it
lacks or adds, and volumes of the stored geometry that the current code does
not build. These are passive in this run, so the warning names those made of
the medium of a sensitive volume (other than vacuum, the medium of the
scoring planes), as they may be detector elements of the design that wrote
the file: they record no hits. Detector IDs come from the node names and copy
numbers of the stored geometry, and the run writes the stored geometry, so
the digitisation and reconstruction see the layout the hits come from.

A detector that the current code cannot build from the stored configuration,
such as the UBT of a file from before the scintillator tiles, is left out of
the run by shipDet_conf.configure, with a warning (warn_left_out): it is not
built, so it registers no sensitive volumes, and its volumes in the stored
geometry are passive.
"""

from __future__ import annotations

from typing import Any

import ROOT

_HELPER = """
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
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

// Names of the volumes.
inline std::unordered_set<std::string> Volumes(TGeoManager* geometry) {
  std::unordered_set<std::string> names;
  TIter next(geometry->GetListOfVolumes());
  while (auto* volume = static_cast<TGeoVolume*>(next())) {
    names.insert(volume->GetName());
  }
  return names;
}

// Names in `a` that `b` lacks.
inline std::vector<std::string> Difference(const std::unordered_set<std::string>& a,
                                           const std::unordered_set<std::string>& b) {
  std::vector<std::string> names;
  for (const auto& name : a) {
    if (!b.count(name)) names.push_back(name);
  }
  return names;
}

inline std::string Placement(TGeoVolume* volume, TGeoNode* node) {
  return std::string(volume->GetName()) + "/" + node->GetName();
}

// Placements ("volume/node") of `a` that `b` lacks, with the name of the
// volume placed, in the volumes that `b` has (the placements in the volumes
// it lacks go with them).
inline std::vector<std::pair<std::string, std::string>> MissingPlacements(TGeoManager* a, TGeoManager* b) {
  std::unordered_set<std::string> have;
  TIter next(b->GetListOfVolumes());
  while (auto* volume = static_cast<TGeoVolume*>(next())) {
    for (Int_t i = 0; i < volume->GetNdaughters(); ++i) have.insert(Placement(volume, volume->GetNode(i)));
  }
  const auto volumes = Volumes(b);
  std::unordered_set<std::string> seen;
  std::vector<std::pair<std::string, std::string>> missing;
  TIter nextA(a->GetListOfVolumes());
  while (auto* volume = static_cast<TGeoVolume*>(nextA())) {
    if (!volumes.count(volume->GetName())) continue;
    for (Int_t i = 0; i < volume->GetNdaughters(); ++i) {
      TGeoNode* node = volume->GetNode(i);
      auto name = Placement(volume, node);
      if (!have.count(name) && seen.insert(name).second) missing.emplace_back(name, node->GetVolume()->GetName());
    }
  }
  return missing;
}

// Name of the medium of a volume, empty for an assembly, a missing volume or
// a vacuum (density below 1e-5 g/cm3, below that of helium at 1.7e-4). The
// scoring planes are sensitive vacuum boxes, so vacuum would otherwise count
// as the medium of a sensitive volume.
inline std::string Medium(TGeoManager* geometry, const char* name) {
  TGeoVolume* volume = geometry->GetVolume(name);
  if (!volume || volume->IsAssembly() || !volume->GetMedium()) return "";
  const TGeoMaterial* material = volume->GetMedium()->GetMaterial();
  if (!material || material->GetDensity() < 1.e-5) return "";
  return volume->GetMedium()->GetName();
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

            # Detectors find their sensitive volumes by name (FairDetector::Initialize).
            sensitive = {str(name) for name in ROOT.pyFairModule.SensitiveVolumeNames()}
            built_names, loaded_names = helper.Volumes(built), helper.Volumes(loaded)
            missing = sorted(str(name) for name in helper.Difference(built_names, loaded_names))
            missing_sensitive = [name for name in missing if name in sensitive]
            if missing_sensitive:
                raise RuntimeError(
                    f"the geometry in {self.geofile} lacks {len(missing_sensitive)} volume(s) that the current code"
                    f" registers as sensitive ({_some(missing_sensitive)}): their detectors would record no hits in"
                    " them. Sensitive volumes are found by name, so a geometry file with another design of a detector"
                    " must keep the names of its sensitive volumes"
                )
            warning = self._differences(helper, built, loaded, built_names, loaded_names, missing, sensitive)

            # Fields attached to volumes are not stored in geometry files.
            built_volumes = list(built.GetListOfVolumes())
            loaded_volumes = list(loaded.GetListOfVolumes())
            same_order = [v.GetName() for v in built_volumes] == [v.GetName() for v in loaded_volumes]
            by_name: dict[str, list[Any]] = {}
            for volume in loaded_volumes:
                by_name.setdefault(volume.GetName(), []).append(volume)
            fields = []
            missing_fields = []
            for i, volume in enumerate(built_volumes):
                field = volume.GetField()
                if not field:
                    continue
                if same_order:
                    target = loaded_volumes[i]
                else:
                    candidates = by_name.get(volume.GetName(), [])
                    if not candidates:
                        missing_fields.append(volume.GetName())
                        continue
                    if len(candidates) != 1:
                        raise RuntimeError(
                            f"cannot tell which of the {len(candidates)} volumes {volume.GetName()} in {self.geofile}"
                            " gets the magnetic field of the volume of that name"
                        )
                    target = candidates[0]
                fields.append((target, field, volume.GetName()))
            if missing_fields:
                raise RuntimeError(
                    f"the geometry in {self.geofile} lacks {len(missing_fields)} volume(s) to which the current code"
                    f" attaches a magnetic field ({_some(missing_fields)}): the field would be lost"
                )
            for target, field, name in fields:
                target.SetField(field)
                self.fields.append(name)

            helper.Use(loaded)
            self.loaded = loaded
            # The parameter file stores the geometry given to FairGeoParSet by FairRunSim::Init().
            geo_par = ROOT.FairRuntimeDb.instance().getContainer("FairGeoParSet")
            if geo_par:
                geo_par.SetGeometry(loaded)
            if warning:
                print(f"WARNING in GeometrySwap: {warning}", flush=True)
            print(
                f"GeometrySwap: transporting through the geometry of {self.geofile} ({len(loaded_volumes)} volumes);"
                f" magnetic fields of volumes copied for: {', '.join(self.fields) or 'none'}",
                flush=True,
            )

        def _differences(
            self,
            helper: Any,
            built: Any,
            loaded: Any,
            built_names: Any,
            loaded_names: Any,
            missing: list[str],
            sensitive: set[str],
        ) -> str | None:
            """Describe how the stored geometry differs from the built one, None if it does not."""
            parts = []
            if missing:
                parts.append(f"lacks {len(missing)} passive volume(s) that the current code builds ({_some(missing)})")
            for verb, a, b in (("lacks", built, loaded), ("has", loaded, built)):
                placements = sorted((str(p.first), str(p.second)) for p in helper.MissingPlacements(a, b))
                if not placements:
                    continue
                of_sensitive = [name for name, placed in placements if placed in sensitive]
                parts.append(
                    f"{verb} {len(placements)} placement(s) that the current code"
                    f" {'builds' if verb == 'lacks' else 'does not build'} ({_some([name for name, _ in placements])})"
                    + (
                        f", {len(of_sensitive)} of them of sensitive volumes ({_some(of_sensitive)}): detector IDs"
                        " follow the stored geometry"
                        if of_sensitive
                        else ""
                    )
                )
            extra = sorted(str(name) for name in helper.Difference(loaded_names, built_names))
            if extra:
                sensitive_media = {str(helper.Medium(built, name)) for name in sensitive} - {""}
                in_sensitive_media = [name for name in extra if str(helper.Medium(loaded, name)) in sensitive_media]
                parts.append(
                    f"has {len(extra)} volume(s) that the current code does not build ({_some(extra)}), which are"
                    " passive in this run"
                    + (
                        f"; {len(in_sensitive_media)} of them are made of the medium of a sensitive volume and"
                        f" record no hits ({_some(in_sensitive_media)})"
                        if in_sensitive_media
                        else ""
                    )
                )
            if not parts:
                return None
            return (
                f"the geometry in {self.geofile} differs from the one the current code builds: it "
                + "; it ".join(parts)
                + ". Particles are transported through the stored geometry."
            )

    return GeometrySwap


def _some(names: list[str], n: int = 10) -> str:
    """The first n names, comma separated."""
    return ", ".join(names[:n]) + (", ..." if len(names) > n else "")


def warn_left_out(geofile: str, left_out: dict[str, str]) -> None:
    """Warn about the modules left out of the run because the current code cannot build them.

    ``left_out`` maps the name of each such module to the reason, a phrase
    describing what geofile has.
    """
    by_reason: dict[str, list[str]] = {}
    for name, reason in left_out.items():
        by_reason.setdefault(reason, []).append(name)
    for reason, names in by_reason.items():
        print(
            f"WARNING: {geofile} has {reason}: {', '.join(names)} left out of this run. They record no hits, and"
            " their volumes in the stored geometry are passive.",
            flush=True,
        )


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
    # configure uses the stored UBT map when there is one, so this only fails
    # if it read UpstreamTagger_config.yaml instead.
    "UpstreamTagger_geo": "UpstreamTagger_config.yaml",
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
