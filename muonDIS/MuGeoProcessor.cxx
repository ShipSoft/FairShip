#include "MuGeoProcessor.h"


MuGeoProcessor::MuGeoProcessor(){


}
  
  /** destructor **/
MuGeoProcessor::~MuGeoProcessor(){
  fPathMap.clear();
}

void MuGeoProcessor::initialise(MuonBranches& aEvt){
  aEvt.mcTrks[0].GetStartVertex(fStartpos);
  fStartT =  aEvt.mcTrks[0].GetStartT();
  aEvt.mcTrks[0].GetMomentum(fStartp);

  aEvt.ubtPt[0].Position(fUBTpos);
  aEvt.ubtPt[0].Momentum(fUBTp);
  fUBTT = aEvt.ubtPt[0].GetTime();

  aEvt.sbtPt[0].Position(fSBTpos);
  aEvt.sbtPt[0].Momentum(fSBTp);
  fSBTT = aEvt.sbtPt[0].GetTime();
  
  aEvt.sstPt[0].Position(fSSTpos);
  aEvt.sstPt[0].Momentum(fSSTp);
  fSSTT = aEvt.sstPt[0].GetTime();

}
  
std::map<std::string,Path> & MuGeoProcessor::FillMuonPath(){

  Path lpath;
  lpath.label = "MS";

  double muonp = fStartp.Mag();
  
  // Initialise start point and direction
  TGeoNode* currentnode = 0;

  fPathMap.clear();
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return fPathMap;
  }
  
  TGeoNode* startnode = gGeoManager->InitTrack(fStartpos.X(),fStartpos.Y(),fStartpos.Z(),fStartp.X()/muonp,fStartp.Y()/muonp,fStartp.Z()/muonp);
  if (!startnode) {
    LOG(error) << "Muon start point out of geometry: x "
               << fStartpos.X() << ", y "
	       << fStartpos.Y() << ", z "
	       << fStartpos.Z();
    return fPathMap;
  }
  TGeoMaterial* material = startnode->GetVolume()->GetMedium()->GetMaterial();
  lpath.volName = startnode->GetVolume()->GetName();
  lpath.density = material->GetDensity();
  lpath.material = material->GetName();
  lpath.startX = fStartpos.X();
  lpath.startY = fStartpos.Y();
  lpath.startZ = fStartpos.Z();
  lpath.startT = fStartT;
  lpath.P = muonp;
  lpath.px = fStartp.X();
  lpath.py = fStartp.Y();
  lpath.pz = fStartp.Z();

  gGeoManager->FindNextBoundary();
  double step = gGeoManager->GetStep();  // Step made
  
  lpath.endZ = lpath.startZ+step;
  
  lpath.init();
  lpath.Print();
  
  auto lele = fPathMap.emplace(lpath.label,lpath);
  if (!lele.second){
    //already exists, add to it
    Path & thepath=lele.first->second;
    thepath.Add(lpath);
  }
  
  return fPathMap;
}
