#ifndef MUFILTERHIT_H
#define MUFILTERHIT_H 1

#include "SndlhcHit.h"
#include "MuFilterPoint.h"
#include "TObject.h"
#include "TVector3.h"

class MuFilterHit : public SndlhcHit
{
  public:

    /** Default constructor **/
    MuFilterHit();
    /** Constructor with hit parameters **/
    MuFilterHit(Int_t detID, Float_t digiLowLeft,Float_t digiLowRight,Float_t digiHighLeft,Float_t digiHighRight);

    // Constructor from MuFilterPoint
    MuFilterHit(int detID,std::vector<MuFilterPoint*>);

 /** Destructor **/
    virtual ~MuFilterHit();

    /** Output to screen **/
    void Print() const;
    /** Getposition **/
    void GetPosition(TVector3 vLeft, TVector3 vRight); // or top and bottom
    Float_t GetEnergy();

    void setInvalid() {flag = false;}
    bool isValid() const {return flag;}
    bool isVertical();
  private:
    /** Copy constructor **/
    MuFilterHit(const MuFilterHit& point);
    MuFilterHit operator=(const MuFilterHit& point);

    Float_t flag;   ///< flag

    ClassDef(MuFilterHit,1);
    

};

#endif
