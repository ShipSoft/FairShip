#ifndef SHIPDATA_SHIPPARTICLE_H_
#define SHIPDATA_SHIPPARTICLE_H_ 1

#include "Rtypes.h"             // for Double_t, Int_t, Double32_t, etc
#include "ShipDetectorList.h"   // for DetectorId
#include "TDatabasePDG.h"       // for TDatabasePDG
#include "TLorentzVector.h"     // for TLorentzVector
#include "TMath.h"              // for Sqrt
#include "TObject.h"            // for TObject
#include "TVector3.h"           // for TVector3

#include <array>   // for std::array

class ShipParticle : public TObject
{

  public:
    /**  Default constructor  **/
    ShipParticle();
    ShipParticle(Int_t pdg,
                 Int_t status,
                 Int_t mother1,
                 Int_t mother2,
                 Int_t daughter1,
                 Int_t daughter2,
                 Double_t px,
                 Double_t py,
                 Double_t pz,
                 Double_t etot,
                 Double_t vx,
                 Double_t vy,
                 Double_t vz,
                 Double_t time);
    ShipParticle(Int_t pdg,
                 Int_t status,
                 Int_t mother1,
                 Int_t mother2,
                 Int_t daughter1,
                 Int_t daughter2,
                 const TLorentzVector& p,
                 const TLorentzVector& v);
    /**  Destructor  **/
    virtual ~ShipParticle();

    /**  Copy constructor  **/
    ShipParticle(const ShipParticle& particle) = default;
    ShipParticle& operator=(const ShipParticle& particle) = default;

    /**  Output to screen  **/
    void Print(Int_t iTrack = 0) const;

    /**  Accessors - particle properties  **/
    Int_t GetPdgCode() const { return fPdgCode; }
    Int_t GetStatusCode() const { return fStatusCode; }
    Int_t GetMother(Int_t i) const { return fMother[i]; }
    Int_t GetFirstMother() const { return fMother[0]; }
    Int_t GetSecondMother() const { return fMother[1]; }
    Int_t GetDaughter(Int_t i) const { return fDaughter[i]; }
    Int_t GetFirstDaughter() const { return fDaughter[0]; }
    Int_t GetLastDaughter() const { return fDaughter[1]; }
    const char* GetName() const override;

    /**  Accessors - momentum  **/
    Double_t Px() const { return fPx; }
    Double_t Py() const { return fPy; }
    Double_t Pz() const { return fPz; }
    Double_t P() const { return TMath::Sqrt(fPx * fPx + fPy * fPy + fPz * fPz); }
    Double_t Pt() const { return TMath::Sqrt(fPx * fPx + fPy * fPy); }
    Double_t Energy() const { return fE; }
    void GetMomentum(TLorentzVector& momentum) const;
    TLorentzVector GetMomentum() const { return TLorentzVector(fPx, fPy, fPz, fE); }
    void Momentum(TLorentzVector& momentum) const { GetMomentum(momentum); }
    Double_t GetMass() const;

    /**  Accessors - vertex  **/
    Double_t Vx() const { return fVx; }
    Double_t Vy() const { return fVy; }
    Double_t Vz() const { return fVz; }
    Double_t T() const { return fVt; }
    void GetVertex(TVector3& vertex) const;
    TVector3 GetVertex() const { return TVector3(fVx, fVy, fVz); }
    void ProductionVertex(TLorentzVector& vertex) const { vertex.SetXYZT(fVx, fVy, fVz, fVt); }

    /**  Accessors - covariance matrices  **/
    // Get momentum covariance matrix elements (4x4 symmetric, 10 unique values)
    const std::array<Double_t, 10>& GetCovP() const { return fCovP; }
    void SetCovP(const Double_t* covElements);
    void SetCovP(const std::array<Double_t, 10>& covElements) { fCovP = covElements; }

    // Get vertex covariance matrix elements (3x3 symmetric, 6 unique values)
    const std::array<Double_t, 6>& GetCovV() const { return fCovV; }
    void SetCovV(const Double_t* covElements);
    void SetCovV(const std::array<Double_t, 6>& covElements) { fCovV = covElements; }

    /**  Distance of closest approach  **/
    Double_t GetDoca() const { return fDoca; }
    void SetDoca(Double_t x) { fDoca = x; }

  private:
    // Particle identification and status
    Int_t fPdgCode;       // PDG code of the particle
    Int_t fStatusCode;    // generation status code
    Int_t fMother[2];     // Indices of the mother particles
    Int_t fDaughter[2];   // Indices of the daughter particles

    // 4-momentum (px, py, pz, E)
    Double_t fPx;   // x component of momentum [GeV]
    Double_t fPy;   // y component of momentum [GeV]
    Double_t fPz;   // z component of momentum [GeV]
    Double_t fE;    // Energy [GeV]

    // 4-vertex (vx, vy, vz, t)
    Double_t fVx;   // x of production vertex [cm]
    Double_t fVy;   // y of production vertex [cm]
    Double_t fVz;   // z of production vertex [cm]
    Double_t fVt;   // t of production vertex [ns]

    // Covariance matrices stored as upper triangular elements
    // fCovP: 4x4 symmetric momentum covariance (10 elements: 0,0; 0,1; 0,2; 0,3; 1,1; 1,2; 1,3; 2,2; 2,3; 3,3)
    std::array<Double_t, 10> fCovP;
    // fCovV: 3x3 symmetric vertex covariance (6 elements: 0,0; 0,1; 0,2; 1,1; 1,2; 2,2)
    std::array<Double_t, 6> fCovV;

    // Distance of closest approach
    Double_t fDoca;

    ClassDef(ShipParticle, 3);
};

#endif   // SHIPDATA_SHIPPARTICLE_H_
