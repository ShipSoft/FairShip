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
    
    Int_t     TrackID()        const {return fTrackID;        }
    Int_t     ElectronID()     const {return fElectronID;     } 
    Int_t     HadronID()       const {return fHadronID;       }
    Int_t     MuonID()         const {return fMuonID;         }
    Int_t     TrackPID()       const {return fTrackPID;       }

    /**       destructor     */
    virtual ~pid();

    void SetTrackID(Int_t b)             { fTrackID=b;       }
    void SetElectronID(Int_t b)          { fElectronID=b;    }
    void SetHadronID(Int_t b)            { fHadronID=b;      }
    void SetMuonID(Int_t b)              { fMuonID=b;        }
    void SetTrackPID(Int_t b)            { fTrackPID=b;      }

  private:

    /** Information to be stored  */

    Int_t        fTrackID;             //  track index 
    Int_t        fElectronID;          //  electron id 
    Int_t        fHadronID;            //  hadron id
    Int_t        fMuonID;              //  muon id
    Int_t        fTrackPID;            //  track pid

    // new version of pid code
    // fTrackPID =  1 -> it is an electron
    // fTrackPID =  2 -> it is a hadron
    // fTrackPID =  3 -> it is a muon
    // fTrackPID = -1 -> informtion is not enough to discuss pid of the track
    // fTrackPID = -2 -> track is outside of pid subdetector acceptance
    // fTrackPID = -3 -> track does not satisfied "FitConverged" or "ndf > 25" cuts 
    // fElectronID = -999
    // fHadronID = -999
    // fMuonID = -999

    // old version of pid code
    // fElectronID (fHadronID or fMuonID) =  1 -> it is a/an electron (hadron or muon); 
    // fElectronID (fHadronID or fMuonID) =  0 -> it is not a/an electron (hadron or muon); 
    // fElectronID (fHadronID or fMuonID) = -1 -> informtion is not enough to discuss;
    // fElectronID (fHadronID or fMuonID) = -2 -> track is outside of pid subdetector acceptance;
    // fElectronID (fHadronID or fMuonID) = -3 -> track does not satisfied "FitConverged" or "ndf > 25" cuts 
    // fTrackPID = -999

    /** container for data points */

    ClassDef(pid,2)
};

#endif //PID_H
