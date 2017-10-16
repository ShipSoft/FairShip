#ifndef PID_H
#define PID_H

#include "TObject.h"
#include "TArrayI.h"
#include "TArrayD.h"

class pid : public TObject
{

  public:

    /**      default constructor    */
    pid(); 
    
      Int_t     TrackID()       const {return fTrackID;}
      Int_t     ElectronID()    const {return fElectronID;} 
      Int_t     HadronID()      const {return fHadronID;}
      Int_t     MuonID()        const {return fMuonID;}

    /**       destructor     */
    virtual ~pid();

    void SetTrackID(Int_t b)             { fTrackID=b;       }
    void SetElectronID(Int_t b)          { fElectronID=b;    }
    void SetHadronID(Int_t b)            { fHadronID=b;      }
    void SetMuonID(Int_t b)              { fMuonID=b;        }

  private:

    /** Information to be stored  */

    Int_t        fTrackID;           //  track index 
    Int_t        fElectronID;          //  electron id 
    Int_t        fHadronID;          //  hadron id
    Int_t        fMuonID;          //  muon id
    // fElectronID (fHadronID or fMuonID) =  1 -> it is a/an electron (hadron or muon); 
    // fElectronID (fHadronID or fMuonID) =  0 -> it is not a/an electron (hadron or muon); 
    // fElectronID (fHadronID or fMuonID) = -1 -> informtion is not enough to discuss;
    // fElectronID (fHadronID or fMuonID) = -2 -> track is outside of pid subdetector acceptance;
    // fElectronID (fHadronID or fMuonID) = -3 -> track does not satisfied "FitConverged" or "ndf > 25" cuts 

    /** container for data points */

    ClassDef(pid,1)
};

#endif //PID_H
