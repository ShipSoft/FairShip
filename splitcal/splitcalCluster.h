#ifndef SPLITCALCLUSTER_H
#define SPLITCALCLUSTER_H 1

#include "splitcalHit.h"
#include <vector> 
//#include <boost/python.hpp>

class splitcalCluster 
{
  public:

    /** Constructors **/
    splitcalCluster();
    //splitcalCluster(boost::python::list& l);
    splitcalCluster(splitcalHit* h);

    /** Destructor **/
    virtual ~splitcalCluster();

    /** Methods **/
    virtual void Print() const;

    void SetEtaPhiE(double& eta, double& phi, double& e) {_eta = eta; _phi = phi; _energy = e;}
    void SetEta(double& eta) {_eta = eta;}
    void SetPhi(double& phi) {_phi = phi;}
    void SetEnergy(double& e) {_energy = e;}
    void SetVectorOfHits(std::vector<splitcalHit* >& v) {_vectorOfHits = v;}
    void AddHit(splitcalHit* h) {_vectorOfHits.push_back(h);}

    double GetEta() {return _eta;}
    double GetPhi() {return _phi;}
    double GetEnergy() {return _energy;}
    std::vector<splitcalHit* >& GetVectorOfHits() {return _vectorOfHits;}

    double SlopeFromLinearRegression(std::vector<double >& x, std::vector<double >& y);
    void ComputeEtaPhiE();


  private:
    /* /\** Copy constructor **\/ */
    /* splitcalCluster(const splitcalCluster& point); */
    /* splitcalCluster operator=(const splitcalCluster& point); */

    double _eta, _phi, _energy;
    std::vector<splitcalHit* > _vectorOfHits;

    ClassDef(splitcalCluster,3);
    
};

#endif
