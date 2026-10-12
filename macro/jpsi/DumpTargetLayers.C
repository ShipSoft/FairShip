// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// DumpTargetLayers.C: read the target slabs (tungsten, molybdenum, tantalum)
// from a FairShip geometry file and write them as a layer file for the J/psi
// generator (JpsiSampler::LoadLayers). Also prints where the target sits in z,
// so the geometry of the data and of the simulation can be compared.
//
//   root -l -b -q
//   'macro/jpsi/DumpTargetLayers.C("<geometry>","target_2018.txt")'
//
// The default geometry is that of the 2018 simulation,
//   /eos/experiment/ship/data/muflux/MC/geofile_full.conical.MuonBack-TGeant4.root
// (the geometry file of the muon-flux data, muflux_geofile.root, has no
// target).
//
// Every node whose material name contains tungsten, molybdenum or tantalum and
// which is at least minWidth (5 cm) wide in x and y is listed with its global z
// range (from its rotated corners); thinner volumes such as the tungsten
// drift-tube wires are skipped. Nodes inside another listed node are skipped (a
// core inside a cladding is kept, the cladding is split around it). Gaps
// between slabs are written as "gap".

#include <algorithm>
#include <cinttypes>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "TFile.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMatrix.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include "TKey.h"
#include "TString.h"

namespace dtl {
struct Slab {
  std::string path;
  std::string mat;
  double z0;
  double z1;
  double A;
  double rho;
  double rmax;
  int depth;
};
bool TargetMaterial(const TString& m) {
  TString s = m;
  s.ToLower();
  return s.Contains("tungsten") || s.Contains("molybd") || s.Contains("tantal");
}
std::string Short(const TString& m) {
  TString s = m;
  s.ToLower();
  if (s.Contains("tungsten")) return "W";
  if (s.Contains("molybd")) return "Mo";
  if (s.Contains("tantal")) return "Ta";
  return m.Data();
}
}  // namespace dtl

void DumpTargetLayers(const char* geofile =
                          "/eos/experiment/ship/data/muflux/MC/"
                          "geofile_full.conical.MuonBack-TGeant4.root",
                      const char* outfile = "target_2018.txt",
                      double minWidth = 5.) {
  using namespace dtl;
  TFile* f = TFile::Open(geofile);
  if (!f || f->IsZombie()) {
    printf("cannot open %s\n", geofile);
    return;
  }
  TGeoManager* geo = nullptr;
  TIter next(f->GetListOfKeys());
  while (TKey* k = static_cast<TKey*>(next()))
    if (std::string(k->GetClassName()) == "TGeoManager")
      geo = static_cast<TGeoManager*>(k->ReadObj());
  if (!geo) {
    printf("no TGeoManager in %s\n", geofile);
    return;
  }
  std::vector<Slab> slabs;
  int64_t nThin = 0;
  TGeoIterator it(geo->GetTopVolume());
  TGeoNode* node;
  while ((node = it())) {
    TGeoVolume* v = node->GetVolume();
    if (!v || !v->GetMaterial() || !TargetMaterial(v->GetMaterial()->GetName()))
      continue;
    TGeoBBox* box = dynamic_cast<TGeoBBox*>(v->GetShape());
    if (!box) continue;
    const TGeoMatrix* m = it.GetCurrentMatrix();
    // global bounding box from the 8 corners (handles rotated volumes, e.g.
    // vertical wires)
    double zlo = 1e30;
    double zhi = -1e30;
    double xlo = 1e30;
    double xhi = -1e30;
    double ylo = 1e30;
    double yhi = -1e30;
    for (int c = 0; c < 8; ++c) {
      double loc[3] = {(c & 1 ? 1 : -1) * box->GetDX(),
                       (c & 2 ? 1 : -1) * box->GetDY(),
                       (c & 4 ? 1 : -1) * box->GetDZ()};
      double glo[3];
      m->LocalToMaster(loc, glo);
      xlo = std::min(xlo, glo[0]);
      xhi = std::max(xhi, glo[0]);
      ylo = std::min(ylo, glo[1]);
      yhi = std::max(yhi, glo[1]);
      zlo = std::min(zlo, glo[2]);
      zhi = std::max(zhi, glo[2]);
    }
    // a target slab is wide across its own axis (local x and y); a wire is thin
    // there, whatever its orientation (stereo wires look wide in global x and
    // y)
    if (2. * std::min(box->GetDX(), box->GetDY()) < minWidth) {
      ++nThin;
      continue;
    }
    TString path;
    it.GetPath(path);
    Slab s;
    s.path = path.Data();
    s.mat = v->GetMaterial()->GetName();
    s.z0 = zlo;
    s.z1 = zhi;
    s.A = v->GetMaterial()->GetA();
    s.rho = v->GetMaterial()->GetDensity();
    s.rmax = 0.5 * std::min(xhi - xlo, yhi - ylo);
    s.depth = it.GetLevel();
    slabs.push_back(s);
  }
  printf("%" PRId64
         " tungsten / molybdenum / tantalum volumes narrower than %.1f cm "
         "skipped (wires etc.)\n",
         nThin, minWidth);
  if (slabs.empty()) {
    printf(
        "no target slabs (W / Mo / Ta, wider than %.1f cm) in %s: this "
        "geometry has no target\n",
        minWidth, geofile);
    return;
  }
  std::sort(slabs.begin(), slabs.end(), [](const Slab& a, const Slab& b) {
    return a.z0 < b.z0 || (a.z0 == b.z0 && a.depth > b.depth);
  });
  printf("%zu target volumes in %s\n", slabs.size(), geofile);
  printf(
      "   z from [cm]   z to [cm]   length    material             A       rho "
      "    half-size  path\n");
  for (const auto& s : slabs)
    printf("   %10.3f  %10.3f  %8.3f   %-18s %7.2f  %6.2f  %8.2f   %s\n", s.z0,
           s.z1, s.z1 - s.z0, s.mat.c_str(), s.A, s.rho, s.rmax,
           s.path.c_str());

  // flatten along z: at each z the innermost (deepest) listed volume wins
  std::vector<double> edges;
  for (const auto& s : slabs) {
    edges.push_back(s.z0);
    edges.push_back(s.z1);
  }
  std::sort(edges.begin(), edges.end());
  edges.erase(
      std::unique(edges.begin(), edges.end(),
                  [](double a, double b) { return std::fabs(a - b) < 1e-6; }),
      edges.end());
  struct Seg {
    double z0;
    double z1;
    const Slab* s;
  };
  std::vector<Seg> segs;
  for (size_t i = 0; i + 1 < edges.size(); ++i) {
    const double zm = 0.5 * (edges[i] + edges[i + 1]);
    const Slab* best = nullptr;
    for (const auto& s : slabs)
      if (zm > s.z0 && zm < s.z1 && (!best || s.depth > best->depth)) best = &s;
    if (!segs.empty() && segs.back().s == best &&
        std::fabs(segs.back().z1 - edges[i]) < 1e-6)
      segs.back().z1 = edges[i + 1];
    else
      segs.push_back({edges[i], edges[i + 1], best});
  }
  while (!segs.empty() && !segs.front().s) segs.erase(segs.begin());
  while (!segs.empty() && !segs.back().s) segs.pop_back();

  FILE* out = fopen(outfile, "w");
  if (!out) {
    printf("cannot write %s\n", outfile);
    return;
  }
  fprintf(out, "# target layers from %s (DumpTargetLayers.C)\n", geofile);
  fprintf(out,
          "# format: zstart <cm> | layer <name> <A> <density g/cm3> <length "
          "cm> | gap <cm>\n");
  fprintf(out, "zstart %.3f\n", segs.front().z0);
  double lenMat[3] = {0, 0, 0};
  double lenGap = 0;
  for (const auto& g : segs) {
    const double len = g.z1 - g.z0;
    if (!g.s) {
      fprintf(out, "gap %.3f\n", len);
      lenGap += len;
      continue;
    }
    const std::string n = Short(g.s->mat);
    fprintf(out, "layer %s %.2f %.3f %.3f\n", n.c_str(), g.s->A, g.s->rho, len);
    lenMat[n == "W" ? 0 : n == "Mo" ? 1 : 2] += len;
  }
  fclose(out);
  printf(
      "\ntarget from z = %.3f to %.3f cm (length %.2f, centre %.2f): W %.2f "
      "cm, Mo %.2f cm, Ta %.2f cm, gaps %.2f cm\n",
      segs.front().z0, segs.back().z1, segs.back().z1 - segs.front().z0,
      0.5 * (segs.front().z0 + segs.back().z1), lenMat[0], lenMat[1], lenMat[2],
      lenGap);
  printf("written %s\n", outfile);
}
