// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

// -------------------------------------------------------------------------
// -----                   ShipParticle source file                   -----
// -------------------------------------------------------------------------
#include "ShipParticle.h"

#include "FairLogger.h"       // for FairLogger, etc
#include "TLorentzVector.h"   // for TLorentzVector
#include "TVector3.h"         // for TVector3

// -----   Default constructor   -------------------------------------------
ShipParticle::ShipParticle()
    : TObject()
    , fPdgCode(0)
    , fStatusCode(0)
    , fMother{0, 0}
    , fDaughter{0, 0}
    , fPx(0.)
    , fPy(0.)
    , fPz(0.)
    , fE(0.)
    , fVx(0.)
    , fVy(0.)
    , fVz(0.)
    , fVt(0.)
    , fCovP{0., 0., 0., 0., 0., 0., 0., 0., 0., 0.}
    , fCovV{0., 0., 0., 0., 0., 0.}
    , fDoca(0.)
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
ShipParticle::ShipParticle(Int_t pdg,
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
                           Double_t time)
    : TObject()
    , fPdgCode(pdg)
    , fStatusCode(status)
    , fMother{mother1, mother2}
    , fDaughter{daughter1, daughter2}
    , fPx(px)
    , fPy(py)
    , fPz(pz)
    , fE(etot)
    , fVx(vx)
    , fVy(vy)
    , fVz(vz)
    , fVt(time)
    , fCovP{0., 0., 0., 0., 0., 0., 0., 0., 0., 0.}
    , fCovV{0., 0., 0., 0., 0., 0.}
    , fDoca(0.)
{}
// -------------------------------------------------------------------------

// -----   Constructor with TLorentzVector   -------------------------------
ShipParticle::ShipParticle(Int_t pdg,
                           Int_t status,
                           Int_t mother1,
                           Int_t mother2,
                           Int_t daughter1,
                           Int_t daughter2,
                           const TLorentzVector& p,
                           const TLorentzVector& v)
    : TObject()
    , fPdgCode(pdg)
    , fStatusCode(status)
    , fMother{mother1, mother2}
    , fDaughter{daughter1, daughter2}
    , fPx(p.Px())
    , fPy(p.Py())
    , fPz(p.Pz())
    , fE(p.E())
    , fVx(v.X())
    , fVy(v.Y())
    , fVz(v.Z())
    , fVt(v.T())
    , fCovP{0., 0., 0., 0., 0., 0., 0., 0., 0., 0.}
    , fCovV{0., 0., 0., 0., 0., 0.}
    , fDoca(0.)
{}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
ShipParticle::~ShipParticle() {}
// -------------------------------------------------------------------------

// -----   Public method SetCovP   -----------------------------------------
void ShipParticle::SetCovP(const Double_t* covElements)
{
    // Set 4x4 symmetric momentum covariance matrix from 10 unique elements
    // Order: (0,0), (0,1), (0,2), (0,3), (1,1), (1,2), (1,3), (2,2), (2,3), (3,3)
    fCovP[0] = covElements[0];   // (0,0)
    fCovP[1] = covElements[1];   // (0,1)
    fCovP[2] = covElements[2];   // (0,2)
    fCovP[3] = covElements[3];   // (0,3)
    fCovP[4] = covElements[4];   // (1,1)
    fCovP[5] = covElements[5];   // (1,2)
    fCovP[6] = covElements[6];   // (1,3)
    fCovP[7] = covElements[7];   // (2,2)
    fCovP[8] = covElements[8];   // (2,3)
    fCovP[9] = covElements[9];   // (3,3)
}
// -------------------------------------------------------------------------

// -----   Public method SetCovV   -----------------------------------------
void ShipParticle::SetCovV(const Double_t* covElements)
{
    // Set 3x3 symmetric vertex covariance matrix from 6 unique elements
    // Order: (0,0), (0,1), (0,2), (1,1), (1,2), (2,2)
    fCovV[0] = covElements[0];   // (0,0)
    fCovV[1] = covElements[1];   // (0,1)
    fCovV[2] = covElements[2];   // (0,2)
    fCovV[3] = covElements[3];   // (1,1)
    fCovV[4] = covElements[4];   // (1,2)
    fCovV[5] = covElements[5];   // (2,2)
}
// -------------------------------------------------------------------------

// -----   Public method GetMomentum   -------------------------------------
void ShipParticle::GetMomentum(TLorentzVector& momentum) const
{
    momentum.SetPxPyPzE(fPx, fPy, fPz, fE);
}
// -------------------------------------------------------------------------

// -----   Public method GetVertex   ---------------------------------------
void ShipParticle::GetVertex(TVector3& vertex) const
{
    vertex.SetXYZ(fVx, fVy, fVz);
}
// -------------------------------------------------------------------------

// -----   Public method GetMass   -----------------------------------------
Double_t ShipParticle::GetMass() const
{
    return TMath::Sqrt(fE * fE - fPx * fPx - fPy * fPy - fPz * fPz);
}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void ShipParticle::Print(Int_t iTrack) const
{
    LOG(info) << "ShipParticle " << iTrack << ":";
    LOG(info) << "  PDG code: " << fPdgCode << ", Status: " << fStatusCode;
    LOG(info) << "  Mothers: " << fMother[0] << ", " << fMother[1];
    LOG(info) << "  Daughters: " << fDaughter[0] << ", " << fDaughter[1];
    LOG(info) << "  Momentum (" << fPx << ", " << fPy << ", " << fPz << ", " << fE << ") GeV";
    LOG(info) << "  Vertex (" << fVx << ", " << fVy << ", " << fVz << ") cm, t = " << fVt << " ns";
    LOG(info) << "  DOCA: " << fDoca << " cm";
}
// -------------------------------------------------------------------------

const char* ShipParticle::GetName() const
{
    // Return particle name based on PDG code
    TParticlePDG* particle = TDatabasePDG::Instance()->GetParticle(fPdgCode);
    if (particle) {
        return particle->GetName();
    }
    return "Unknown";
}
// -------------------------------------------------------------------------
