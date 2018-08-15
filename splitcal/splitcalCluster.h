#ifndef SPLITCALCLUSTER_H
#define SPLITCALCLUSTER_H 1

#include "splitcalHit.h"
#include <vector> 

class splitcalCluster 
{
  public:

    /** Constructors **/
    splitcalCluster();
    splitcalCluster(std::vector<splitcalHit >& v);

    /** Destructor **/
    virtual ~splitcalCluster();

    /** Methods **/
    virtual void Print() const;

    void SetEtaPhiE(double& eta, double& phi, double& e) {_eta = eta; _phi = phi; _energy = e;}
    void SetEta(double& eta) {_eta = eta;}
    void SetPhi(double& phi) {_phi = phi;}
    void SetEnergy(double& e) {_energy = e;}
    void SetVectorOfHits(std::vector<splitcalHit >& v) {_vectorOfHit = v;}

    double GetEta() {return _eta;}
    double GetPhi() {return _phi;}
    double GetEnergy() {return _energy;}
    std::vector<splitcalHit >& GetVectorOfHits() {return _vectorOfHits;}

    double SlopeFromLinearRegression(std::vector<double >& x, std::vector<double >& y);


  private:
    /* /\** Copy constructor **\/ */
    /* splitcalCluster(const splitcalCluster& point); */
    /* splitcalCluster operator=(const splitcalCluster& point); */

    double _eta, _phi, _energy;
    std::vector<splitcalHit > _vectorOfHits;

    ClassDef(splitcalCluster,3);
    
};

#endif
