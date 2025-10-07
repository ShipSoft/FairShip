// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#ifndef SPLITCAL_SPLITCALCLUSTER_H_
#define SPLITCAL_SPLITCALCLUSTER_H_

#include "TObject.h"              //

#include "splitcalHit.h"
#include <array>
#include <vector>
//#include <boost/python.hpp>

// ROOT headers
/* #include <TLorentzVector.h> */
#include <TVector3.h>

struct regression
{

  double slope;
  double slopeError;
  double intercept;
  double interceptError;

};


class splitcalCluster : public TObject
{
  public:

    /** Constructors **/
    splitcalCluster();
    //splitcalCluster(boost::python::list& l);

    /** Destructor **/
    virtual ~splitcalCluster();

    /** Methods **/
    virtual void Print() const;

    void SetEtaPhiE(double& eta, double& phi, double& e) {_eta = eta; _phi = phi; _energy = e;}
    void SetEta(double& eta) {_eta = eta;}
    void SetPhi(double& phi) {_phi = phi;}
    void SetEnergy(double& e) {_energy = e;}
    void SetIndex(int i) {_index = i;}
    void SetStartPoint(const double& x, const double& y, const double& z) {_start[0] = x; _start[1] = y; _start[2] = z; }
    void SetEndPoint(const double& x, const double& y, const double& z) {_end[0] = x; _end[1] = y; _end[2] = z; }
    void SetHitIndices(const std::vector<int>& v) {_hitIndices = v;}
    void AddHit(int hitIndex, double weight = 1.0) {
        _hitIndices.push_back(hitIndex);
        _hitWeights.push_back(weight);
    }

    int GetIndex() {return _index;}
    double GetEta() {return _eta;}
    double GetPhi() {return _phi;}
    double GetEnergy() {return _energy;}
    double GetPx() {return _energy*sin(_eta)*cos(_phi);}
    double GetPy() {return _energy*sin(_eta)*sin(_phi);}
    double GetPz() {return _energy*cos(_eta);}
    double GetEx() {return GetPx();}
    double GetEy() {return GetPy();}
    double GetEz() {return GetPz();}
    TVector3 GetStartPoint() const {return TVector3(_start[0], _start[1], _start[2]); }
    TVector3 GetEndPoint() const {return TVector3(_end[0], _end[1], _end[2]); }
    const std::vector<int>& GetHitIndices() const {return _hitIndices;}
    const std::vector<double>& GetHitWeights() const {return _hitWeights;}

    regression LinearRegression(std::vector<double >& x, std::vector<double >& y);
    void ComputeEtaPhiE(const std::vector<splitcalHit>& hits);

    // temporary for test
    double GetSlopeZX() {return _mZX;}
    double GetInterceptZX() {return _qZX;}
    double GetSlopeZY() {return _mZY;}
    double GetInterceptZY() {return _qZY;}

    /** Copy constructor **/
    splitcalCluster(const splitcalCluster& cluster) = default;
    splitcalCluster& operator=(const splitcalCluster& cluster) = default;
  private:

    int _index;
    double _eta, _phi, _energy;
    std::array<double, 3> _start;
    std::array<double, 3> _end;
    std::vector<int> _hitIndices;
    std::vector<double> _hitWeights;

    // temporary for test
    double _mZX, _qZX;
    double _mZY, _qZY;

    ClassDef(splitcalCluster,3);

};

#endif  // SPLITCAL_SPLITCALCLUSTER_H_
