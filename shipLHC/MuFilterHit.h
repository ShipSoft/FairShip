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
    MuFilterHit(Int_t detID);
    // Constructor from MuFilterPoint
    MuFilterHit(int detID,std::vector<MuFilterPoint*>);

 /** Destructor **/
    virtual ~MuFilterHit();

    /** Output to screen **/
    void Print() const;
    Float_t GetEnergy();

    void setInvalid() {flag = false;}
    bool isValid() const {return flag;}
    bool isVertical();
  private:
    /** Copy constructor **/
    MuFilterHit(const MuFilterHit& hit);
    MuFilterHit operator=(const MuFilterHit& hit);

    Float_t flag;   ///< flag

    ClassDef(MuFilterHit,1);
    

};

#endif
