// -------------------------------------------------------------------------
// -----                   ShipParticle source file                   -----
// -------------------------------------------------------------------------
#include "ShipParticle.h"

#include "FairLogger.h"                 // for FairLogger, etc

#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TParticle.h"                  // for TParticle
#include "TParticlePDG.h"               // for TParticlePDG

// -----   Default constructor   -------------------------------------------
ShipParticle::ShipParticle()
  : TParticle()
{
}
// -------------------------------------------------------------------------
ShipParticle::ShipParticle(Int_t pdg,  Int_t status,
       Int_t mother1,   Int_t mother2,
       Int_t daughter1, Int_t daughter2,
       Double_t px, Double_t py, Double_t pz, Double_t etot,
       Double_t vx, Double_t vy, Double_t vz, Double_t time):TParticle(pdg, status,mother1,mother2,daughter1,daughter2,
       px, py, pz, etot, vx, vy, vz, time),
       fCovP(TMatrixDSym(4)),
       fCovV(TMatrixDSym(3))
 {
 doca = 0.;   
 }

ShipParticle::ShipParticle(Int_t pdg,  Int_t status,
      Int_t mother1,   Int_t mother2,
      Int_t daughter1, Int_t daughter2,
      const TLorentzVector &p,
      const TLorentzVector &v):TParticle(pdg, status,mother1,mother2,daughter1,daughter2,p,v),
       fCovP(TMatrixDSym(4)),
       fCovV(TMatrixDSym(3))
 {
 doca = 0.;   
 }

// -----   Destructor   ----------------------------------------------------
ShipParticle::~ShipParticle() {
 }
// -------------------------------------------------------------------------


// -----   Public method Set CovP CovV  -----------------------------------------

void ShipParticle::SetCovP(Double_t* covElements)
{
   fCovP(0,0) = covElements[0];
   fCovP(0,1) = covElements[1];
   fCovP(0,2) = covElements[2];
   fCovP(0,3) = covElements[3];
   
   fCovP(1,0) = covElements[1];
   fCovP(1,1) = covElements[4];
   fCovP(1,2) = covElements[5];
   fCovP(1,3) = covElements[6];
   
   fCovP(2,0) = covElements[2];
   fCovP(2,1) = covElements[5];
   fCovP(2,2) = covElements[7];
   fCovP(2,3) = covElements[8];
   
   
   fCovP(3,0) = covElements[3];
   fCovP(3,1) = covElements[6];
   fCovP(3,2) = covElements[8];
   fCovP(3,3) = covElements[9];
   
   
}
// -----   Public method Set/GetCovV   -----------------------------------------
void ShipParticle::SetCovV(Double_t* covElements)
{
   fCovV(0,0) = covElements[0];
   fCovV(0,1) = covElements[1];
   fCovV(0,2) = covElements[2];
   fCovV(1,1) = covElements[3];
   fCovV(1,2) = covElements[4];
   fCovV(2,2) = covElements[5];
   fCovV(1,0) = covElements[1];
   fCovV(2,0) = covElements[2];
   fCovV(2,1) = covElements[4];
}
// -------------------------------------------------------------------------
void ShipParticle::GetMomentum(TLorentzVector& momentum)
{
  momentum.SetPxPyPzE(fPx,fPy,fPz,fE);
}
void ShipParticle::GetVertex(TVector3& vx)
{
  vx.SetXYZ(fVx,fVy,fVz);
}
Double_t ShipParticle::GetMass()
{
 TLorentzVector momentum;
 GetMomentum(momentum);
 return momentum.M();
}
ClassImp(ShipParticle)
