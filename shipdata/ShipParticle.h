// -------------------------------------------------------------------------
// -----                      ShipParticle header file                  -----
// -------------------------------------------------------------------------


/** ShipParticle.h
 ** Data class for storing Monte Carlo tracks processed by the ShipStack.
 ** A MCTrack can be a primary track put into the simulation or a
 ** secondary one produced by the transport through decay or interaction.
 **/


#ifndef ShipParticle_H
#define ShipParticle_H 1

#include "TParticle.h"                  // for TParticle
#include "ShipDetectorList.h"           // for DetectorId
#include "Rtypes.h"                     // for Double_t, Int_t, Double32_t, etc
#include "TLorentzVector.h"             // for TLorentzVector
#include "TMath.h"                      // for Sqrt
#include "TVector3.h"                   // for TVector3
#include "TMatrixDSym.h"                //

class TParticle;

class ShipParticle : public TParticle
{

  public:


    /**  Default constructor  **/
    ShipParticle();
    ShipParticle(Int_t pdg,  Int_t status,
       Int_t mother1,   Int_t mother2,
       Int_t daughter1, Int_t daughter2,
       Double_t px, Double_t py, Double_t pz, Double_t etot,
       Double_t vx, Double_t vy, Double_t vz, Double_t time);
    ShipParticle(Int_t pdg,  Int_t status,
      Int_t mother1,   Int_t mother2,
      Int_t daughter1, Int_t daughter2,
      const TLorentzVector &p,
      const TLorentzVector &v);
    /**  Destructor  **/
    virtual ~ShipParticle();

    /**  Output to screen  **/
    void Print(Int_t iTrack=0) const;

    /**  Accessors  **/
    void GetMomentum(TLorentzVector& momentum);
    Double_t GetMass();
    void GetVertex(TVector3& vertex);
    TMatrixDSym*  GetCovP();
    TMatrixDSym*  GetCovV();
    void SetCovP(Double_t *x);
    void SetCovV(Double_t *x);
    Double_t GetDoca()  const { return doca; }
    void SetDoca(Double_t x) {doca=x;}
  private:
    TMatrixDSym  fCovP;
    TMatrixDSym  fCovV;
    Double_t doca;
    ClassDef(ShipParticle,2);
};

// ==========   Inline functions   ========================================


inline TMatrixDSym* ShipParticle::GetCovP()
{
  return  &fCovP;
}


inline TMatrixDSym* ShipParticle::GetCovV()
{
  return  &fCovV;
}


#endif
