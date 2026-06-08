#include "MuGeoProcessor.h"


MuGeoProcessor::MuGeoProcessor(){
    fhasUBThit=false;
    fhasSBThit=false;
    fhasSSThit=false;
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
  double snext = 0;
  unsigned lcount = 0;
  double zpos = fStartpos.Z();
  bool changeU=true;
  bool changeS=true;
  bool changeT=true;
  
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

    //reset start info
    if (lpath.label == "MS") lpath.SetStartInfo(fStartpos,fStartp,fStartT);
    else if (lpath.label == "UBT") {
      lpath.SetStartInfo(fUBTpos,fUBTp,fUBTT);
      muonp = fUBTp.Mag();
      if (changeU) currentnode = gGeoManager->InitTrack(fUBTpos.X(),fUBTpos.Y(),fUBTpos.Z(),fUBTp.X()/muonp,fUBTp.Y()/muonp,fUBTp.Z()/muonp);
      changeU=false;
    }
    else if (lpath.label == "SBT") {
      lpath.SetStartInfo(fSBTpos,fSBTp,fSBTT);
      muonp = fSBTp.Mag();
      if (changeS) currentnode = gGeoManager->InitTrack(fSBTpos.X(),fSBTpos.Y(),fSBTpos.Z(),fSBTp.X()/muonp,fSBTp.Y()/muonp,fSBTp.Z()/muonp);
      changeS=false;
    }
    else if (lpath.label == "SST") {
      lpath.SetStartInfo(fSSTpos,fSSTp,fSSTT);
      muonp = fSSTp.Mag();
      if (changeT) currentnode = gGeoManager->InitTrack(fSSTpos.X(),fSSTpos.Y(),fSSTpos.Z(),fSSTp.X()/muonp,fSSTp.Y()/muonp,fSSTp.Z()/muonp);
      changeT=false;
    }
    if (!currentnode) {
      LOG(error) << "Muon point out of geometry: x "
		 << lpath.startX << ", y "
		 << lpath.startY << ", z "
		 << lpath.startZ << ", direction: "
		 << lpath.px/muonp << ","
		 << lpath.py/muonp << ","
		 << lpath.pz/muonp;
      break;
    }
    std::ostringstream lInfo;
    lInfo << currentnode->GetVolume()->GetName() << " "
	  << material->GetName()
	  << " start zpos = " << zpos << " cm";
    currentnode = gGeoManager->FindNextBoundaryAndStep();
    snext = gGeoManager->GetStep();
    lInfo << " step " << snext;
    LOG(debug) << lInfo.str();
  
    lpath.endZ = lpath.startZ+snext;
    lpath.init();
    lpath.Print();
  
    zpos += snext;
    auto lele = fPathMap.emplace(lpath.label,lpath);
    if (!lele.second){
      //already exists, add to it
      Path & thepath=lele.first->second;
      thepath.Add(lpath);
    }

    
    //for safety...
    if (lcount > 1000) break;
    lcount++;
  }


  return fPathMap;
}
