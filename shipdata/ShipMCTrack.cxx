// -------------------------------------------------------------------------
// -----                   ShipMCTrack source file                   -----
// -------------------------------------------------------------------------
#include "ShipMCTrack.h"

#include "FairLogger.h"                 // for FairLogger, etc

#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TParticle.h"                  // for TParticle
#include "TParticlePDG.h"               // for TParticlePDG

// -----   Default constructor   -------------------------------------------
ShipMCTrack::ShipMCTrack()
    : TObject()
    , fPdgCode(0)
    , fMotherId(-1)
    , fPx(0.)
    , fPy(0.)
    , fPz(0.)
    , fM(-1.)
    , fStartX(0.)
    , fStartY(0.)
    , fStartZ(0.)
    , fStartT(0.)
    , fW(1.)
    , fProcID(44)
    , fNPoints(0)
    , fTrackID(0)
{
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
ShipMCTrack::ShipMCTrack(Int_t pdgCode,
                         Int_t motherId,
                         Double_t px,
                         Double_t py,
                         Double_t pz,
                         Double_t M,
                         Double_t x,
                         Double_t y,
                         Double_t z,
                         Double_t t,
                         Int_t nPoints,
                         Int_t trackID,
                         Double_t w)
    : TObject()
    , fPdgCode(pdgCode)
    , fMotherId(motherId)
    , fPx(px)
    , fPy(py)
    , fPz(pz)
    , fM(M)
    , fStartX(x)
    , fStartY(y)
    , fStartZ(z)
    , fStartT(t)
    , fW(w)
    , fProcID(44)
    , fNPoints(nPoints)
    , fTrackID(trackID)
{
}
// -------------------------------------------------------------------------



// -----   Copy constructor   ----------------------------------------------
ShipMCTrack::ShipMCTrack(const ShipMCTrack& track)
    : TObject(track)
    , fPdgCode(track.fPdgCode)
    , fMotherId(track.fMotherId)
    , fPx(track.fPx)
    , fPy(track.fPy)
    , fPz(track.fPz)
    , fM(track.fM)
    , fStartX(track.fStartX)
    , fStartY(track.fStartY)
    , fStartZ(track.fStartZ)
    , fStartT(track.fStartT)
    , fW(track.GetWeight())
    , fProcID(track.GetProcID())
    , fNPoints(track.fNPoints)
    , fTrackID(track.fTrackID)
{
}
// -------------------------------------------------------------------------



// -----   Constructor from TParticle   ------------------------------------
ShipMCTrack::ShipMCTrack(TParticle* part)
    : TObject()
    , fPdgCode(part->GetPdgCode())
    , fMotherId(part->GetMother(0))
    , fPx(part->Px())
    , fPy(part->Py())
    , fPz(part->Pz())
    , fM(TMath::Sqrt(part->Energy() * part->Energy() - part->P() * part->P()))
    , fStartX(part->Vx())
    , fStartY(part->Vy())
    , fStartZ(part->Vz())
    , fStartT(part->T() * 1e09)
    , fW(part->GetWeight())
    , fProcID(part->GetUniqueID())
    , fNPoints(0)
{
}
// -------------------------------------------------------------------------



// -----   Destructor   ----------------------------------------------------
ShipMCTrack::~ShipMCTrack() { }
// -------------------------------------------------------------------------



// -----   Public method Print   -------------------------------------------
void ShipMCTrack::Print(Int_t trackId) const
{
  LOG(debug) << "Track " << trackId << ", mother : " << fMotherId << ", Type "
             << fPdgCode << ", momentum (" << fPx << ", " << fPy << ", "
             << fPz << ") GeV" ;
 /* LOG(DEBUG2) << "       Ref " << GetNPoints(kREF)
              << ", TutDet " << GetNPoints(kTutDet)
              << ", Rutherford " << GetNPoints(kFairRutherford) ;
*/
}
// -------------------------------------------------------------------------
// -----   Public method GetEnergy   -----------------------------------------

Double_t ShipMCTrack::GetEnergy() const
{
  if (fM<0){
// older data, mass not made persistent
   Double_t mass = GetMass();
   return TMath::Sqrt(mass*mass + fPx*fPx + fPy*fPy + fPz*fPz );
  }else{
   return TMath::Sqrt(fM*fM + fPx*fPx + fPy*fPy + fPz*fPz );
  }
}
// -----   Public method GetMass   -----------------------------------------
Double_t ShipMCTrack::GetMass() const
{
  if (fM<0){
// older data, mass not made persistent
   if ( TDatabasePDG::Instance() ) {
    TParticlePDG* particle = TDatabasePDG::Instance()->GetParticle(fPdgCode);
    if ( particle ) { return particle->Mass(); }
    else { return 0.; }
   }
  }
  return fM;
}
// -------------------------------------------------------------------------


// -----   Public method GetWeight   -------------------------------------
Double_t ShipMCTrack::GetWeight() const
{
  return fW;
}
// -------------------------------------------------------------------------


// -----   Public method GetRapidity   -------------------------------------
Double_t ShipMCTrack::GetRapidity() const
{
  Double_t e = GetEnergy();
  Double_t y = 0.5 * TMath::Log( (e+fPz) / (e-fPz) );
  return y;
}
// -------------------------------------------------------------------------




// -----   Public method GetNPoints   --------------------------------------
Int_t ShipMCTrack::GetNPoints(DetectorId detId) const
{
/*  // TODO: Where does this come from
  if      ( detId == kREF  ) { return (  fNPoints &   1); }
  else if ( detId == kTutDet  ) { return ( (fNPoints & ( 7 <<  1) ) >>  1); }
  else if ( detId == kFairRutherford ) { return ( (fNPoints & (31 <<  4) ) >>  4); }
  else {
    LOG(error) << "Unknown detector ID " << detId ;
    return 0;
  }
*/
   return 0;
}
// -------------------------------------------------------------------------



// -----   Public method SetNPoints   --------------------------------------
void ShipMCTrack::SetNPoints(Int_t iDet, Int_t nPoints)
{
/*
  if ( iDet == kREF ) {
    if      ( nPoints < 0 ) { nPoints = 0; }
    else if ( nPoints > 1 ) { nPoints = 1; }
    fNPoints = ( fNPoints & ( ~ 1 ) )  |  nPoints;
  }

  else if ( iDet == kTutDet ) {
    if      ( nPoints < 0 ) { nPoints = 0; }
    else if ( nPoints > 7 ) { nPoints = 7; }
    fNPoints = ( fNPoints & ( ~ (  7 <<  1 ) ) )  |  ( nPoints <<  1 );
  }

  else if ( iDet == kFairRutherford ) {
    if      ( nPoints <  0 ) { nPoints =  0; }
    else if ( nPoints > 31 ) { nPoints = 31; }
    fNPoints = ( fNPoints & ( ~ ( 31 <<  4 ) ) )  |  ( nPoints <<  4 );
  }

  else LOG(error) << "Unknown detector ID "  << iDet ;
*/
}

void ShipMCTrack::SetTrackID(Int_t trackID){
    fTrackID = trackID;
}
// -------------------------------------------------------------------------
