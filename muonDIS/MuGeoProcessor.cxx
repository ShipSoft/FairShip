#include "MuGeoProcessor.h"

MuGeoProcessor::MuGeoProcessor() {
  fZmax = 14000;
  fZmin = 2500;
  fhasUBThit = false;
  fhasSBThit = false;
  fhasSSThit = false;
  TVector3 nulVec(0, 0, 0);
  fStartpos = nulVec;
  fStartp = nulVec;
  fStartT = 0;
  fUBTpos = nulVec;
  fUBTp = nulVec;
  fUBTT = 0;
  fSBTpos = nulVec;
  fSBTp = nulVec;
  fSBTT = 0;
  fSSTpos = nulVec;
  fSSTp = nulVec;
  fSSTT = 0;
  fZmaxMap.clear();
  fVolMap.clear();
}

/** destructor **/
MuGeoProcessor::~MuGeoProcessor() {
  fPathMap.clear();
  fZmaxMap.clear();
  fVolMap.clear();
}

void MuGeoProcessor::initialise(MuonBranches& aEvt) {
  if (aEvt.mcTrks.size() > 0) {
    aEvt.mcTrks[0].GetStartVertex(fStartpos);
    fStartT = aEvt.mcTrks[0].GetStartT();
    aEvt.mcTrks[0].GetMomentum(fStartp);
  }
  if (aEvt.ubtPt.size() > 0) {
    fhasUBThit = true;
    aEvt.ubtPt[0].Position(fUBTpos);
    aEvt.ubtPt[0].Momentum(fUBTp);
    fUBTT = aEvt.ubtPt[0].GetTime();
  }
  if (aEvt.sbtPt.size() > 0) {
    fhasSBThit = true;
    aEvt.sbtPt[0].Position(fSBTpos);
    aEvt.sbtPt[0].Momentum(fSBTp);
    fSBTT = aEvt.sbtPt[0].GetTime();
  }
  if (aEvt.sstPt.size() > 0) {
    fhasSSThit = true;
    aEvt.sstPt[0].Position(fSSTpos);
    aEvt.sstPt[0].Momentum(fSSTp);
    fSSTT = aEvt.sstPt[0].GetTime();
  }
  // @FIXME-AM what to do if startpos is greater than UBTpos, protect ?
  // extract intersections
  fVtx12 = GetVertex(fStartpos, fStartp, fUBTpos, fUBTp);
  fVtx13 = GetVertex(fStartpos, fStartp, fSBTpos, fSBTp);
  fVtx14 = GetVertex(fStartpos, fStartp, fSSTpos, fSSTp);
  fVtx23 = GetVertex(fUBTpos, fUBTp, fSBTpos, fSBTp);
  fVtx24 = GetVertex(fUBTpos, fUBTp, fSSTpos, fSSTp);
  fVtx34 = GetVertex(fSBTpos, fSBTp, fSSTpos, fSSTp);
}

TVector3 MuGeoProcessor::GetVertex(const TVector3& r1, const TVector3& p1,
                                   const TVector3& r2, const TVector3& p2) {
  TVector3 nulVec(0, 0, 0);
  if (r1.Z() == 0 || r2.Z() == 0) return nulVec;

  TVector3 u1 = p1.Unit();
  TVector3 u2 = p2.Unit();

  TVector3 w0 = r1 - r2;

  double a = u1 * u1;
  double b = u1 * u2;
  double c = u2 * u2;

  double d = u1 * w0;
  double e = u2 * w0;

  double denom = a * c - b * b;

  // Protect against nearly parallel tracks
  if (std::abs(denom) < 1e-12) {
    LOG(warning) << "GetVertex(): nearly parallel tracks (denominator = "
                 << denom << "). Returning first measurement.";
    return r1;
  }

  double t = (b * e - c * d) / denom;
  double s = (a * e - b * d) / denom;

  TVector3 poca1 = r1 + t * u1;
  TVector3 poca2 = r2 + s * u2;

  TVector3 vertex = 0.5 * (poca1 + poca2);

  double zmin = std::min(r1.Z(), r2.Z());
  double zmax = std::max(r1.Z(), r2.Z());

  // Clamp the POCA to the measured interval
  if (vertex.Z() < zmin) {
    return (r1.Z() < r2.Z()) ? r1 : r2;
  }

  if (vertex.Z() > zmax) {
    return (r1.Z() > r2.Z()) ? r1 : r2;
  }

  return vertex;
}


void MuGeoProcessor::FillZmaxVolumes() {
  fZmaxMap.clear();
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return;
  }
  double zStart = 400; //approx. end of HA
  TGeoNode* startnode = gGeoManager->InitTrack(0,0,zStart,0,0,1);
  if (!startnode) {
    LOG(error) << "Muon start point out of geometry: (0,0," << zStart << "), going along z ";
    return;
  }

  TGeoNode* currentnode = gGeoManager->GetCurrentNode();
  std::string volName = currentnode->GetVolume()->GetName();
  double snext = zStart;
  unsigned lcount = 0;
  bool foundMS = false;
  bool foundUBT = false;
  while (currentnode) {
    volName = currentnode->GetVolume()->GetName();
    if (volName.find("Magn") != volName.npos) foundMS = true;
    if (volName.find("Upstream") != volName.npos) foundUBT = true;
    currentnode = gGeoManager->FindNextBoundaryAndStep();
    snext += gGeoManager->GetStep();
    LOG(info) << "Volume: " << volName << ", end z = " << snext; 
    volName = currentnode->GetVolume()->GetName();
    //@FIXME AMM-avoid hardcoding, pass by config ?
    if (foundMS && volName.find("Magn") == volName.npos){
      LOG(info) << " Found end of magnet at z = " << snext;
      fZmaxMap.emplace("MS",snext);
      foundMS = false;
    }
    if (foundUBT && volName.find("Upstream") == volName.npos){
      LOG(info) << " Found end of Upstream detector at z = " << snext;
      fZmaxMap.emplace("UBT",snext);
      break;
    }
    // for safety...
    if (lcount > 1000) {
      LOG(info) << "Reached 1000 iterations in checking all volumes, stopping there: z=" << snext;
      break;
    }
    lcount++;
  }

  if (fZmaxMap.size() != 2){
    LOG(info) << " Warning, map size is : " << fZmaxMap.size() << ", did not find the maximum z position of MS and UBT, will be using Zmax= " << fZmax << " parameter.";
  }
  
}

void MuGeoProcessor::CheckAllVolumes() {
  std::map<std::string, double> lMap;
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
  }

  double z = fZmin;
  double step = 50;
  double stepd = 0.1;
  int nS = 8;
  int nSD = 10;
  for (int ix(-nS); ix < nS + 1; ++ix) {
    for (int iy(-nS); iy < nS + 1; ++iy) {
      for (int idx(-nSD); idx < nSD + 1; ++idx) {
        for (int idy(-nSD); idy < nSD + 1; ++idy) {
          if (pow(idx * stepd, 2) + pow(idy * stepd, 2) > 1) continue;
          double dz = sqrt(1 - pow(idx * stepd, 2) - pow(idy * stepd, 2));
          TGeoNode* startnode = gGeoManager->InitTrack(
              ix * step, iy * step, z, idx * stepd, idy * stepd, dz);
          if (!startnode) {
            LOG(error) << "Muon start point out of geometry: " << ix * step
                       << " " << iy * step << " " << z << " " << idx * stepd
                       << " " << idy * stepd << " " << dz;
          }
          TGeoNode* currentnode = gGeoManager->GetCurrentNode();
          double snext = z;
          unsigned lcount = 0;

          while (currentnode) {
            std::string material =
                currentnode->GetVolume()->GetMedium()->GetMaterial()->GetName();
            std::string volName = currentnode->GetVolume()->GetName();
            // if (volName.find("Tr2") != volName.npos) break;
            volName.append("_");
            volName.append(material);
            lMap.emplace(volName, snext);
            currentnode = gGeoManager->FindNextBoundaryAndStep();
            snext += gGeoManager->GetStep() * dz;

            // for safety...
            if (lcount > 1000) {
	      LOG(info) << "Reached 1000 iterations in checking all volumes, stopping there: z=" << snext << " cm, x=" << ix * step
                       << " y=" << iy * step << " z=" << z << " dir_x=" << idx * stepd
                       << " dir_y=" << idy * stepd << " dir_z=" << dz;
	      break;
	    }
	    lcount++;
          }
        }
      }
    }
  }

  LOG(info) << " -- All volumes found in geometry: n=" << lMap.size();
  for (auto lele = lMap.begin(); lele != lMap.end(); ++lele) {
    LOG(info) << lele->first << " " << lele->second;
  }
}

std::map<std::string, MuonPath>& MuGeoProcessor::FillMuonPath() {
  fPathMap.clear();
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return fPathMap;
  }

  // Initialise start point and direction
  double muonp = fStartp.Mag();
  if (muonp == 0) {
    LOG(error) << "Muon has momentum " << muonp << ", not filling path";
    return fPathMap;
  }

  if (fStartpos.Z()<fZmin){
    LOG(error) << " This muon has a starting Z position of " << fStartpos.Z() << " before the minimum to be considered: " << fZmin
	       << "==> not filling path, please adapt minimum position or muon input.";
    return fPathMap;
  }

  TGeoNode* startnode = gGeoManager->InitTrack(
      fStartpos.X(), fStartpos.Y(), fStartpos.Z(), fStartp.X() / muonp,
      fStartp.Y() / muonp, fStartp.Z() / muonp);
  if (!startnode) {
    LOG(error) << "Muon start point out of geometry: x " << fStartpos.X()
               << ", y " << fStartpos.Y() << ", z " << fStartpos.Z()
               << ", direction: " << fStartp.X() / muonp << ","
               << fStartp.Y() / muonp << "," << fStartp.Z() / muonp;
    return fPathMap;
  }

  TGeoNode* currentnode = gGeoManager->GetCurrentNode();
  double znext = 0;
  unsigned lcount = 0;
  double zpos = fStartpos.Z();
  // Fill a vector with position of all points of closest approach for the
  // trajectories, points at which we want to reinitialise the direction with
  // the measurement provided by veto and SST hits.
  std::vector<TVector3> vtxVec;
  std::vector<TVector3> startVec;
  std::vector<TVector3> dirVec;
  std::vector<double> timeVec;
  vtxVec.push_back(fStartpos);
  timeVec.push_back(fStartT);
  startVec.push_back(fStartpos);
  dirVec.push_back(fStartp);
  if (fhasUBThit) {
    vtxVec.push_back(fVtx12);
    timeVec.push_back(fUBTT);
    startVec.push_back(fUBTpos);
    dirVec.push_back(fUBTp);
  } else if (fhasSBThit) {
    vtxVec.push_back(fVtx13);
    timeVec.push_back(fSBTT);
    startVec.push_back(fSBTpos);
    dirVec.push_back(fSBTp);
  } else if (fhasSSThit) {
    vtxVec.push_back(fVtx14);
    timeVec.push_back(fSSTT);
    startVec.push_back(fSSTpos);
    dirVec.push_back(fSSTp);
  }
  if (fhasUBThit && fhasSBThit) {
    vtxVec.push_back(fVtx23);
    timeVec.push_back(fSBTT);
    startVec.push_back(fSBTpos);
    dirVec.push_back(fSBTp);
  } else if (fhasUBThit && fhasSSThit) {
    vtxVec.push_back(fVtx24);
    timeVec.push_back(fSSTT);
    startVec.push_back(fSSTpos);
    dirVec.push_back(fSSTp);
  }
  if (fhasSBThit && fhasSSThit) {
    vtxVec.push_back(fVtx34);
    timeVec.push_back(fSSTT);
    startVec.push_back(fSSTpos);
    dirVec.push_back(fSSTp);
  }

  //Only want to fill DIS in the pre-decay volume material if muon trajectory does not go through SBT nor SST
  //bool stopAtMS = false;
  //bool stopAtUBT = false;
  //if (!fhasSBThit && !fhasSSThit) {
  //if (fhasUBThit) stopAtUBT = true;
  //if (!fhasUBThit) stopAtMS = true;
  //}
  
  std::vector<bool> doInit;
  unsigned nVtx = vtxVec.size();
  for (unsigned iV(0); iV < nVtx; ++iV) {
    doInit.push_back(true);
  }

  LOG(debug) << " Number of vertices found to change track direction: " << nVtx;

  unsigned iV = 0;

  while (currentnode) {
    //stop early to not waste time propagating a muon that goes out of acceptance.
    //if (stopAtUBT && zpos > FindZmax("UBT")) break;
    //if (stopAtMS && zpos > FindZmax("MS")) break;
    
    // stop when reaching input config zmax position
    if (zpos > fZmax) break;
    
    TGeoMaterial* material =
        currentnode->GetVolume()->GetMedium()->GetMaterial();
    std::string lvolName = currentnode->GetVolume()->GetName();
    const Double_t* lpos = gGeoManager->GetCurrentPoint();

    TVector3 currentPos(lpos[0], lpos[1], lpos[2]);

    muonp = dirVec[iV].Mag();
    if (muonp == 0) {
      LOG(error) << "Muon has momentum " << muonp << ", stop filling path";
      break;
    }

    if (doInit[iV]) {
      currentnode =
          gGeoManager->InitTrack(vtxVec[iV].X(), vtxVec[iV].Y(), vtxVec[iV].Z(),
                                 dirVec[iV].X() / muonp, dirVec[iV].Y() / muonp,
                                 dirVec[iV].Z() / muonp);
      material = currentnode->GetVolume()->GetMedium()->GetMaterial();
      LOG(debug) << " ---> Update track direction at z=" << zpos;
      doInit[iV] = false;
    }

    if (!currentnode) {
      LOG(error) << "Muon point out of geometry: x " << vtxVec[iV].X() << ", y "
                 << vtxVec[iV].Y() << ", z " << vtxVec[iV].Z()
                 << ", direction: " << dirVec[iV].X() / muonp << ","
                 << dirVec[iV].Y() / muonp << "," << dirVec[iV].Z() / muonp;
      break;
    }
    std::ostringstream lInfo;
    lInfo << currentnode->GetVolume()->GetName() << " " << material->GetName()
          << " start zpos = " << zpos << " cm";
    double nextL = 0;
    bool switchVtx = true;
    if (iV + 1 < nVtx) {
      lInfo << " Current vtx: " << vtxVec[iV].X() << " " << vtxVec[iV].Y()
            << " " << vtxVec[iV].Z();
      lInfo << " Next vtx: " << vtxVec[iV + 1].X() << " " << vtxVec[iV + 1].Y()
            << " " << vtxVec[iV + 1].Z();
      lInfo << " Current pos: " << currentPos.X() << " " << currentPos.Y()
            << " " << currentPos.Z();
      nextL = (vtxVec[iV + 1] - currentPos).Mag();
      if (nextL != nextL) nextL = 0;
      if (nextL > 0)
        currentnode = gGeoManager->FindNextBoundaryAndStep(nextL, kFALSE);
      else
        currentnode = gGeoManager->FindNextBoundaryAndStep();
      double step = gGeoManager->GetStep();
      lInfo << " Vtx-Vtx length 3D: " << nextL << " step taken " << step;
      if (nextL > 0 && step < nextL) switchVtx = false;
    } else
      currentnode = gGeoManager->FindNextBoundaryAndStep();
    double step = gGeoManager->GetStep();
    znext = step * dirVec[iV].Z() / muonp;
    lInfo << " end zpos = " << zpos + znext << " stepz " << znext << " step3D "
          << step;
    LOG(debug) << lInfo.str();

    // create new path object
    MuonPath lpath;
    lpath.AddVolume(lvolName, material->GetName(), material->GetDensity());
    // reset vertex info to closest measured point
    lpath.SetVertexInfo(startVec[iV], dirVec[iV], timeVec[iV]);
    lpath.SetLength(step, currentPos, znext);
    lpath.Print();

    //Sanity check: fill a map to print at the end a unique list of volumes found for each label.
    fVolMap[lpath.GetLabel()].insert(lvolName+"_"+material->GetName());
    
    zpos += znext;
    auto lele = fPathMap.emplace(lpath.GetLabel(), lpath);
    if (!lele.second) {
      // already exists, add to it
      MuonPath& thepath = lele.first->second;
      thepath.Add(lpath);
    }
    // increment vtx index to go to next change in direction...
    if (iV < nVtx - 1 && switchVtx) iV++;
    // for safety...
    if (lcount > 1000) {
      LOG(info) << "Reached 1000 iterations in filling path, stopping there: z=" << zpos << " cm";
      break;
    }
    lcount++;
  }

  LOG(debug) << " -- Map elements after " << lcount << "steps: n=" << fPathMap.size();
  for (auto lele = fPathMap.begin(); lele != fPathMap.end(); ++lele) {
    LOG(debug) << lele->first << ": ";
    lele->second.Print();
  }
  
  return fPathMap;
}

void MuGeoProcessor::PrintVolumes(){ 
  LOG(info) << " -- Volume Map elements: size=" << fVolMap.size();
  for (const auto& [label, volumes] : fVolMap) {
    LOG(info) << label << ":";
    for (const auto& volume : volumes) {
      LOG(info) << "  " << volume;
    }
  }
}
