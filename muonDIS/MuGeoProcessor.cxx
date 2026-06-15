#include "MuGeoProcessor.h"


MuGeoProcessor::MuGeoProcessor(){
    fhasUBThit=false;
    fhasSBThit=false;
    fhasSSThit=false;
    TVector3 nulVec(0,0,0);
    fStartpos = nulVec;
    fStartp = nulVec;
    fStartT=0;
    fUBTpos = nulVec;
    fUBTp = nulVec;
    fUBTT=0;
    fSBTpos = nulVec;
    fSBTp = nulVec;
    fSBTT=0;
    fSSTpos = nulVec;
    fSSTp = nulVec;
    fSSTT=0;
}
  
  /** destructor **/
MuGeoProcessor::~MuGeoProcessor(){
  fPathMap.clear();
}

void MuGeoProcessor::initialise(MuonBranches& aEvt){
  if (aEvt.mcTrks.size()>0){
    aEvt.mcTrks[0].GetStartVertex(fStartpos);
    fStartT =  aEvt.mcTrks[0].GetStartT();
    aEvt.mcTrks[0].GetMomentum(fStartp);
  }
  if (aEvt.ubtPt.size()>0){
    fhasUBThit=true;
    aEvt.ubtPt[0].Position(fUBTpos);
    aEvt.ubtPt[0].Momentum(fUBTp);
    fUBTT = aEvt.ubtPt[0].GetTime();
  }
  if (aEvt.sbtPt.size()>0){
    fhasSBThit=true;
    aEvt.sbtPt[0].Position(fSBTpos);
    aEvt.sbtPt[0].Momentum(fSBTp);
    fSBTT = aEvt.sbtPt[0].GetTime();
  }
  if (aEvt.sstPt.size()>0){
    fhasSSThit=true;
    aEvt.sstPt[0].Position(fSSTpos);
    aEvt.sstPt[0].Momentum(fSSTp);
    fSSTT = aEvt.sstPt[0].GetTime();
  }

  //extract intersections
  fVtx12 = GetVertex(fStartpos,fStartp,fUBTpos,fUBTp);
  fVtx13 = GetVertex(fStartpos,fStartp,fSBTpos,fSBTp);
  fVtx14 = GetVertex(fStartpos,fStartp,fSSTpos,fSSTp);
  fVtx23 = GetVertex(fUBTpos,fUBTp,fSBTpos,fSBTp);
  fVtx24 = GetVertex(fUBTpos,fUBTp,fSSTpos,fSSTp);
  fVtx34 = GetVertex(fSBTpos,fSBTp,fSSTpos,fSSTp);
}

TVector3 MuGeoProcessor::GetVertex(const TVector3 & r1, const TVector3 & p1,
				   const TVector3 & r2, const TVector3 & p2){
  TVector3 nulVec(0,0,0);
  if (r1.Z()==0 || r2.Z()==0) return nulVec;
  
  TVector3 u1 = p1.Unit();
  TVector3 u2 = p2.Unit();

  TVector3 w0 = r1-r2;
  
  double a = u1*u1;
  double b = u1*u2;
  double c = u2*u2;
  
  double d = u1*w0;
  double e = u2*w0;
  
  double t = (b*e-c*d)/(a*c-b*b);
  double s = (a*e-b*d)/(a*c-b*b);
  
  TVector3 poca1 = r1 + t*u1;
  TVector3 poca2 = r2 + s*u2;
  
  return 0.5*(poca1+poca2);

}

void MuGeoProcessor::CheckAllVolumes(){

  std::map<std::string,double> lMap;
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
  }
  
  double z=3131;
  double step = 50;
  double stepd = 0.1;
  int nS = 8;
  int nSD = 10;
  for (int ix(-nS);ix<nS+1;++ix){
    for (int iy(-nS);iy<nS+1;++iy){
      for (int idx(-nSD);idx<nSD+1;++idx){
	for (int idy(-nSD);idy<nSD+1;++idy){
	  if (pow(idx*stepd,2)+pow(idy*stepd,2)>1) continue;
	  double dz = sqrt(1-pow(idx*stepd,2)-pow(idy*stepd,2));
	  TGeoNode* startnode = gGeoManager->InitTrack(ix*step,iy*step,z,idx*stepd,idy*stepd,dz);
	  if (!startnode) {
	    LOG(error) << "Muon start point out of geometry: "
		       << ix*step << " " << iy*step << " " << z << " "
		       << idx*stepd << " " << idy*stepd << " " << dz;
	  }
	  TGeoNode* currentnode = gGeoManager->GetCurrentNode();
	  double snext = z;
	  unsigned lcount = 0;
	  
	  while(currentnode) {
	    std::string material = currentnode->GetVolume()->GetMedium()->GetMaterial()->GetName();
	    std::string volName = currentnode->GetVolume()->GetName();
	    if (volName.find("Tr2") != volName.npos) break;
	    volName.append("_");
	    volName.append(material);
	    lMap.emplace(volName,snext);
	    currentnode = gGeoManager->FindNextBoundaryAndStep();
	    snext += gGeoManager->GetStep()*dz;
	    
	    //for safety...
	    if (lcount > 1000) break;
	    lcount++;
	  }
	}
      }
    }
  }
  
  LOG(info) << " -- All volumes found in geometry: n=" << lMap.size();
  for (auto lele=lMap.begin();lele!=lMap.end();++lele){
    LOG(info) << lele->first << " " << lele->second;
  }
  
}


std::map<std::string,Path> & MuGeoProcessor::FillMuonPath(){

  fPathMap.clear();
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return fPathMap;
  }
  
  // Initialise start point and direction
  double muonp = fStartp.Mag();
  TGeoNode* startnode = gGeoManager->InitTrack(fStartpos.X(),fStartpos.Y(),fStartpos.Z(),fStartp.X()/muonp,fStartp.Y()/muonp,fStartp.Z()/muonp);
  if (!startnode) {
    LOG(error) << "Muon start point out of geometry: x "
               << fStartpos.X() << ", y "
	       << fStartpos.Y() << ", z "
	       << fStartpos.Z() << ", direction: "
	       << fStartp.X()/muonp << ","
	       << fStartp.Y()/muonp << ","
	       << fStartp.Z()/muonp;
    return fPathMap;
  }
  
  TGeoNode* currentnode = gGeoManager->GetCurrentNode();
  double znext = 0;
  unsigned lcount = 0;
  double zpos = fStartpos.Z();

  //Fill a vector with position of all points of closest approach for the trajectories,
  //points at which we want to reinitialise the direction with the measurement provided by veto and SST hits.
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
  }
  else if (fhasSBThit) {
    vtxVec.push_back(fVtx13);
    timeVec.push_back(fSBTT);
    startVec.push_back(fSBTpos);
    dirVec.push_back(fSBTp);
  }
  else if (fhasSSThit) {
    vtxVec.push_back(fVtx14);
    timeVec.push_back(fSSTT);
    startVec.push_back(fSSTpos);
    dirVec.push_back(fSSTp);
  }
  if (fhasUBThit && fhasSBThit){
    vtxVec.push_back(fVtx23);
    timeVec.push_back(fSBTT);
    startVec.push_back(fSBTpos);
    dirVec.push_back(fSBTp);
  }
  else if (fhasUBThit && fhasSSThit){
    vtxVec.push_back(fVtx24);
    timeVec.push_back(fSSTT);
    startVec.push_back(fSSTpos);
    dirVec.push_back(fSSTp);
  }
  if (fhasSBThit && fhasSSThit){
    vtxVec.push_back(fVtx34);
    timeVec.push_back(fSSTT);
    startVec.push_back(fSSTpos);
    dirVec.push_back(fSSTp);
  }

  
  std::vector<bool> doInit;
  unsigned nVtx = vtxVec.size();
  for (unsigned iV(0);iV<nVtx;++iV){
    doInit.push_back(true);
  }

  LOG(info) << " Number of vertices found to change track direction: " << nVtx;
  
  unsigned iV = 0;

  while(currentnode) {
    TGeoMaterial* material = currentnode->GetVolume()->GetMedium()->GetMaterial();
    Path lpath;
    lpath.volName = currentnode->GetVolume()->GetName();

    //stop when reaching SST2
    if (lpath.volName.find("Tr2") != lpath.volName.npos) break;
    
    lpath.density = material->GetDensity();
    lpath.material = material->GetName();
    lpath.startZ = zpos;
    lpath.label = lpath.GetLabel(lpath.volName,lpath.material);

    //reset vertex info to closest measured point
    lpath.SetVertexInfo(startVec[iV],dirVec[iV],timeVec[iV]);
    muonp = dirVec[iV].Mag();
    
    TVector3 currentPos(lpath.startX,lpath.startY,lpath.startZ);

    if (doInit[iV]) {
      currentnode = gGeoManager->InitTrack(vtxVec[iV].X(),vtxVec[iV].Y(),vtxVec[iV].Z(),dirVec[iV].X()/muonp,dirVec[iV].Y()/muonp,dirVec[iV].Z()/muonp);
      LOG(debug) << " ---> Update track direction at z=" << zpos;
      doInit[iV] = false;
    }
    
    if (!currentnode) {
      LOG(error) << "Muon point out of geometry: x "
		 << vtxVec[iV].X() << ", y "
		 << vtxVec[iV].Y() << ", z "
		 << vtxVec[iV].Z() << ", direction: "
		 << lpath.px/muonp << ","
		 << lpath.py/muonp << ","
		 << lpath.pz/muonp;
      break;
    }
    std::ostringstream lInfo;
    lInfo << currentnode->GetVolume()->GetName() << " "
	  << material->GetName()
	  << " start zpos = " << zpos << " cm";
    double nextL = 0;
    bool switchVtx = true;
    if (iV+1<nVtx) {
      lInfo << " Current vtx: " << vtxVec[iV].X() << " " << vtxVec[iV].Y() << " " << vtxVec[iV].Z();
      lInfo << " Next vtx: " << vtxVec[iV+1].X() << " " << vtxVec[iV+1].Y() << " " << vtxVec[iV+1].Z();
      lInfo << " Current pos: " << currentPos.X() << " " << currentPos.Y() << " " << currentPos.Z();
      nextL = (vtxVec[iV+1]-currentPos).Mag();
      if (nextL!=nextL) nextL = 0;
      if (nextL>0) currentnode = gGeoManager->FindNextBoundaryAndStep(nextL,kFALSE);
      else currentnode = gGeoManager->FindNextBoundaryAndStep();
      double step = gGeoManager->GetStep();
      lInfo << " Vtx-Vtx length 3D: " << nextL << " step taken " << step;
      if (nextL>0 && step<nextL) switchVtx = false;
    }
    else currentnode = gGeoManager->FindNextBoundaryAndStep();
    znext = gGeoManager->GetStep()*lpath.pz/muonp;
    lInfo << " end zpos = " << zpos+znext << " stepz " << znext << " step3D " << gGeoManager->GetStep();
    LOG(debug) << lInfo.str();

    lpath.endZ = lpath.startZ+znext;
    lpath.init();
    lpath.Print();
  
    zpos += znext;
    auto lele = fPathMap.emplace(lpath.label,lpath);
    if (!lele.second){
      //already exists, add to it
      Path & thepath=lele.first->second;
      thepath.Add(lpath);
    }
    //increment vtx index to go to next change in direction...
    if (iV < nVtx-1 && switchVtx) iV++;
    //for safety...
    if (lcount > 1000) break;
    lcount++;
  }


  LOG(debug) << " -- Map elements: n=" << fPathMap.size();
  for (auto lele=fPathMap.begin();lele!=fPathMap.end();++lele){
    LOG(debug) << lele->first << ": ";
    lele->second.Print();
  }
  
  return fPathMap;
}
