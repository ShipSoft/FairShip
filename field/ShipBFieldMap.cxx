// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

/*! \class ShipBFieldMap
  \brief Class that defines a (3d) magnetic field map (distances in cm, fields
  in tesla)

  \author John Back <J.J.Back@warwick.ac.uk>
*/

#include "ShipBFieldMap.h"

#include <fstream>
#include <iostream>

#include "FairLogger.h"  /// for FairLogger, MESSAGE_ORIGIN
#include "TFile.h"
#include "TTree.h"

ShipBFieldMap::ShipBFieldMap(const std::string& label,
                             const std::string& mapFileName, Float_t xOffset,
                             Float_t yOffset, Float_t zOffset, Float_t phi,
                             Float_t theta, Float_t psi, Float_t scale,
                             Bool_t isSymmetric)
    : TVirtualMagField(label.c_str()),
      fieldMap_(new floatArray()),
      mapFileName_(mapFileName),
      initialised_(kFALSE),
      isCopy_(kFALSE),
      Nx_(0),
      Ny_(0),
      Nz_(0),
      N_(0),
      xMin_(0.0),
      xMax_(0.0),
      dx_(0.0),
      xRange_(0.0),
      yMin_(0.0),
      yMax_(0.0),
      dy_(0.0),
      yRange_(0.0),
      zMin_(0.0),
      zMax_(0.0),
      dz_(0.0),
      zRange_(0.0),
      xOffset_(xOffset),
      yOffset_(yOffset),
      zOffset_(zOffset),
      phi_(phi),
      theta_(theta),
      psi_(psi),
      scale_(scale),
      isSymmetric_(isSymmetric),
      theTrans_(nullptr),
      Tesla_(10.0) {
  this->initialise();
}

ShipBFieldMap::~ShipBFieldMap() {
  // Delete the internal vector storing the field map values
  if (fieldMap_ && isCopy_ == kFALSE) {
    delete fieldMap_;
    fieldMap_ = nullptr;
  }

  if (theTrans_) {
    delete theTrans_;
    theTrans_ = nullptr;
  }
}

ShipBFieldMap::ShipBFieldMap(const std::string& newName,
                             const ShipBFieldMap& rhs, Float_t newXOffset,
                             Float_t newYOffset, Float_t newZOffset,
                             Float_t newPhi, Float_t newTheta, Float_t newPsi,
                             Float_t newScale)
    : TVirtualMagField(newName.c_str()),
      fieldMap_(rhs.fieldMap_),
      mapFileName_(rhs.GetMapFileName()),
      initialised_(kFALSE),
      isCopy_(kTRUE),
      Nx_(rhs.Nx_),
      Ny_(rhs.Ny_),
      Nz_(rhs.Nz_),
      N_(rhs.N_),
      xMin_(rhs.xMin_),
      xMax_(rhs.xMax_),
      dx_(rhs.dx_),
      xRange_(rhs.xRange_),
      yMin_(rhs.yMin_),
      yMax_(rhs.yMax_),
      dy_(rhs.dy_),
      yRange_(rhs.yRange_),
      zMin_(rhs.zMin_),
      zMax_(rhs.zMax_),
      dz_(rhs.dz_),
      zRange_(rhs.zRange_),
      xOffset_(newXOffset),
      yOffset_(newYOffset),
      zOffset_(newZOffset),
      phi_(newPhi),
      theta_(newTheta),
      psi_(newPsi),
      scale_(newScale),
      isSymmetric_(rhs.isSymmetric_),
      theTrans_(nullptr),
      Tesla_(10.0) {
  // Copy constructor with new label and different global offset, which uses
  // the same field map data (pointer) and distance units as the rhs object
  this->initialise();
}

void ShipBFieldMap::Field(const Double_t* position, Double_t* B) {
  // Set the B field components given the global position coordinates

  // Convert the global position into a local one for the volume field.
  // Initialise the local co-ords, which will get overwritten if the
  // coordinate transformation exists. For a global field, any local
  // volume transformation is ignored
  Double_t localCoords[3] = {position[0], position[1], position[2]};

  if (theTrans_) {
    theTrans_->MasterToLocal(position, localCoords);
  }

  // The local position coordinates
  Float_t x = localCoords[0];
  Float_t y = localCoords[1];
  Float_t z = localCoords[2];

  // Now check to see if we have x-y quadrant symmetry (z has no symmetry):
  // Bx is antisymmetric in both x and y, By is symmetric in both, while Bz is
  // symmetric in x but antisymmetric in y (dipole physics). So Bx can change
  // sign for x < 0 or y < 0, and Bz can change sign for y < 0:
  // 1. x > 0, y > 0: Bx = +Bx, Bz = +Bz
  // 2. x > 0, y < 0: Bx = -Bx, Bz = -Bz
  // 3. x < 0, y > 0: Bx = -Bx, Bz = +Bz
  // 4. x < 0, y < 0: Bx = +Bx, Bz = -Bz

  Float_t BxSign(1.0);
  Float_t BzSign = 1;

  if (isSymmetric_) {
    // The field map coordinates only contain x > 0 and y > 0, i.e. we
    // are using x-y quadrant symmetry. If the local x or y coordinates
    // are negative we need to change their sign and keep track of the
    // adjusted sign of Bx which we use as a multiplication factor at the end
    if (x < 0.0) {
      x = -x;
      BxSign *= -1.0;
    }

    if (y < 0.0) {
      y = -y;
      BxSign *= -1.0;
      BzSign = -1.0;
    }
  }

  // Initialise the B field components to zero
  B[0] = 0.0;
  B[1] = 0.0;
  B[2] = 0.0;

  // First check to see if we are inside the field map range
  Bool_t inside = this->insideRange(x, y, z);
  if (inside == kFALSE) {
    return;
  }

  // Find the neighbouring bins for the given point
  binPair xBinInfo = this->getBinInfo(x, ShipBFieldMap::xAxis);
  binPair yBinInfo = this->getBinInfo(y, ShipBFieldMap::yAxis);
  binPair zBinInfo = this->getBinInfo(z, ShipBFieldMap::zAxis);

  Int_t iX = xBinInfo.first;
  Int_t iY = yBinInfo.first;
  Int_t iZ = zBinInfo.first;

  // Check that the bins are valid
  if (iX == -1 || iY == -1 || iZ == -1) {
    return;
  }

  // Get the various neighbouring bin entries
  Int_t iX1(iX + 1);
  Int_t iY1(iY + 1);
  Int_t iZ1(iZ + 1);

  const Int_t binA = this->getMapBin(iX, iY, iZ);
  const Int_t binB = this->getMapBin(iX1, iY, iZ);
  const Int_t binC = this->getMapBin(iX, iY1, iZ);
  const Int_t binD = this->getMapBin(iX1, iY1, iZ);
  const Int_t binE = this->getMapBin(iX, iY, iZ1);
  const Int_t binF = this->getMapBin(iX1, iY, iZ1);
  const Int_t binG = this->getMapBin(iX, iY1, iZ1);
  const Int_t binH = this->getMapBin(iX1, iY1, iZ1);

  // Retrieve the fractional bin distances and their complements
  const Float_t xFrac = xBinInfo.second;
  const Float_t yFrac = yBinInfo.second;
  const Float_t zFrac = zBinInfo.second;
  const Float_t xFrac1 = 1.0 - xFrac;
  const Float_t yFrac1 = 1.0 - yFrac;
  const Float_t zFrac1 = 1.0 - zFrac;

  if (!fieldMap_) {
    return;
  }

  // Fetch each of the eight corner triples once and interpolate all three
  // field components in a single pass (trilinear interpolation), then scale
  // with the appropriate multiplication factor (default = 1.0).
  const floatArray& fm = *fieldMap_;
  const std::array<Float_t, 3>& cA = fm[binA];
  const std::array<Float_t, 3>& cB = fm[binB];
  const std::array<Float_t, 3>& cC = fm[binC];
  const std::array<Float_t, 3>& cD = fm[binD];
  const std::array<Float_t, 3>& cE = fm[binE];
  const std::array<Float_t, 3>& cF = fm[binF];
  const std::array<Float_t, 3>& cG = fm[binG];
  const std::array<Float_t, 3>& cH = fm[binH];

  Float_t Bc[3];
  for (Int_t i = 0; i < 3; ++i) {
    Bc[i] = triLinearInterp(cA[i], cB[i], cC[i], cD[i], cE[i], cF[i], cG[i],
                            cH[i], xFrac, xFrac1, yFrac, yFrac1, zFrac, zFrac1);
  }

  B[0] = Bc[0] * scale_ * BxSign;
  B[1] = Bc[1] * scale_;
  B[2] = Bc[2] * scale_ * BzSign;
}

void ShipBFieldMap::initialise() {
  if (initialised_ == kFALSE) {
    if (isCopy_ == kFALSE) {
      this->readMapFile();
    }

    // Set the global coordinate translation and rotation info
    if (fabs(phi_) > 1e-6 || fabs(theta_) > 1e-6 || fabs(psi_) > 1e-6) {
      // We have non-zero rotation angles. Create a combined translation and
      // rotation
      TGeoTranslation tr("offsets", xOffset_, yOffset_, zOffset_);
      TGeoRotation rot("angles", phi_, theta_, psi_);
      theTrans_ = new TGeoCombiTrans(tr, rot);

    } else {
      // We only need a translation
      theTrans_ = new TGeoTranslation("offsets", xOffset_, yOffset_, zOffset_);
    }

    initialised_ = kTRUE;
  }
}

void ShipBFieldMap::readMapFile() {
  LOG(info) << "ShipBFieldMap::readMapFile() creating field " << this->GetName()
            << " using file " << mapFileName_;

  // Check to see if we have a ROOT file
  if (mapFileName_.find(".root") != std::string::npos) {
    this->readRootFile();

  } else {
    this->readTextFile();
  }
}

void ShipBFieldMap::readRootFile() {
  TFile* theFile = TFile::Open(mapFileName_.c_str());

  if (!theFile) {
    LOG(fatal) << "ShipBFieldMap: could not find the file " << mapFileName_;
  }

  // Coordinate ranges
  TTree* rTree = dynamic_cast<TTree*>(theFile->Get("Range"));
  if (!rTree) {
    LOG(fatal) << "ShipBFieldMap: could not find Range tree in "
               << mapFileName_;
  }

  rTree->SetBranchAddress("xMin", &xMin_);
  rTree->SetBranchAddress("xMax", &xMax_);
  rTree->SetBranchAddress("dx", &dx_);
  rTree->SetBranchAddress("yMin", &yMin_);
  rTree->SetBranchAddress("yMax", &yMax_);
  rTree->SetBranchAddress("dy", &dy_);
  rTree->SetBranchAddress("zMin", &zMin_);
  rTree->SetBranchAddress("zMax", &zMax_);
  rTree->SetBranchAddress("dz", &dz_);

  // Fill the ranges
  rTree->GetEntry(0);

  this->setLimits();

  // Make sure we don't have a copy
  if (isCopy_ == kFALSE) {
    // The data is expected to contain Bx,By,Bz data values
    // in ascending z,y,x coordinate order

    TTree* dTree = dynamic_cast<TTree*>(theFile->Get("Data"));
    if (!dTree) {
      LOG(fatal) << "ShipBFieldMap: could not find Data tree in "
                 << mapFileName_;
    }

    Float_t Bx, By, Bz;
    // Only enable the field components
    dTree->SetBranchStatus("*", 0);
    dTree->SetBranchStatus("Bx", 1);
    dTree->SetBranchStatus("By", 1);
    dTree->SetBranchStatus("Bz", 1);

    dTree->SetBranchAddress("Bx", &Bx);
    dTree->SetBranchAddress("By", &By);
    dTree->SetBranchAddress("Bz", &Bz);

    Int_t nEntries = dTree->GetEntries();
    if (nEntries != N_) {
      LOG(fatal) << "Expected " << N_ << " field map entries but found "
                 << nEntries;
      nEntries = 0;
    }

    fieldMap_->reserve(nEntries);

    for (Int_t i = 0; i < nEntries; i++) {
      dTree->GetEntry(i);

      // B field values are in Tesla. This means these values are multiplied
      // by a factor of ten since both FairRoot and the VMC interface use kGauss
      Bx *= Tesla_;
      By *= Tesla_;
      Bz *= Tesla_;

      // Store the B field 3-vector
      fieldMap_->push_back({Bx, By, Bz});
    }
  }

  theFile->Close();
}

void ShipBFieldMap::readTextFile() {
  std::ifstream getData(mapFileName_.c_str());

  if (!getData.is_open()) {
    LOG(fatal) << "Error: Cannot open magnetic field map file: "
               << mapFileName_;
  }

  std::string tmpString("");

  getData >> tmpString >> xMin_ >> xMax_ >> dx_ >> yMin_ >> yMax_ >> dy_ >>
      zMin_ >> zMax_ >> dz_;

  this->setLimits();

  // Check to see if this object is a "copy"
  if (isCopy_ == kFALSE) {
    // Read the field map and store the magnetic field components

    // Second line can be ignored since they are
    // just labels for the data columns for readability
    getData >> tmpString >> tmpString >> tmpString;

    // The remaining lines contain Bx,By,Bz data values
    // in ascending z,y,x co-ord order
    fieldMap_->reserve(N_);

    Float_t Bx(0.0), By(0.0), Bz(0.0);

    for (Int_t i = 0; i < N_; i++) {
      getData >> Bx >> By >> Bz;

      // B field values are in Tesla. This means these values are multiplied
      // by a factor of ten since both FairRoot and the VMC interface use kGauss
      Bx *= Tesla_;
      By *= Tesla_;
      Bz *= Tesla_;

      // Store the B field 3-vector
      fieldMap_->push_back({Bx, By, Bz});
    }
  }

  getData.close();
}

Bool_t ShipBFieldMap::insideRange(Float_t x, Float_t y, Float_t z) {
  Bool_t inside(kFALSE);

  if (x >= xMin_ && x <= xMax_ && y >= yMin_ && y <= yMax_ && z >= zMin_ &&
      z <= zMax_) {
    inside = kTRUE;
  }

  return inside;
}

void ShipBFieldMap::setLimits() {
  // Since the default SHIP distance unit is cm, we do not need to convert
  // these map limits, i.e. cm = 1 already

  xRange_ = xMax_ - xMin_;
  yRange_ = yMax_ - yMin_;
  zRange_ = zMax_ - zMin_;

  // Find the number of bins using the limits and bin sizes. The number of bins
  // includes both the minimum and maximum values. To ensure correct rounding
  // up to the nearest integer we need to add 1.5 not 1.0.
  if (dx_ > 0.0) {
    Nx_ = static_cast<Int_t>(((xMax_ - xMin_) / dx_) + 1.5);
  }
  if (dy_ > 0.0) {
    Ny_ = static_cast<Int_t>(((yMax_ - yMin_) / dy_) + 1.5);
  }
  if (dz_ > 0.0) {
    Nz_ = static_cast<Int_t>(((zMax_ - zMin_) / dz_) + 1.5);
  }

  N_ = Nx_ * Ny_ * Nz_;

  LOG(info) << "x limits: " << xMin_ << ", " << xMax_ << ", dx = " << dx_;
  LOG(info) << "y limits: " << yMin_ << ", " << yMax_ << ", dy = " << dy_;
  LOG(info) << "z limits: " << zMin_ << ", " << zMax_ << ", dz = " << dz_;

  LOG(info) << "Offsets: x = " << xOffset_ << ", y = " << yOffset_
            << ", z = " << zOffset_;
  LOG(info) << "Angles : phi = " << phi_ << ", theta = " << theta_
            << ", psi = " << psi_;

  LOG(info) << "Total number of bins = " << N_ << "; Nx = " << Nx_
            << ", Ny = " << Ny_ << ", Nz = " << Nz_;
}

ShipBFieldMap::binPair ShipBFieldMap::getBinInfo(
    Float_t u, ShipBFieldMap::CoordAxis theAxis) {
  Float_t du(0.0), uMin(0.0);
  Int_t Nu(0);

  if (theAxis == ShipBFieldMap::xAxis) {
    du = dx_;
    uMin = xMin_;
    Nu = Nx_;
  } else if (theAxis == ShipBFieldMap::yAxis) {
    du = dy_;
    uMin = yMin_;
    Nu = Ny_;
  } else if (theAxis == ShipBFieldMap::zAxis) {
    du = dz_;
    uMin = zMin_;
    Nu = Nz_;
  }

  Int_t iBin(-1);
  Float_t fracL(0.0);

  if (du > 1e-10) {
    // Get the number of fractional bin widths the point is from the first
    // volume bin
    Float_t dist = (u - uMin) / du;
    // Get the integer equivalent of this distance, which is the bin number
    iBin = static_cast<Int_t>(dist);
    // Get the actual fractional distance of the point from the leftmost bin
    // edge
    fracL = (dist - iBin * 1.0);
  }

  // Check that the bin number is valid
  if (iBin < 0 || iBin >= Nu) {
    iBin = -1;
    fracL = 0.0;
  } else if (iBin >= Nu - 1) {
    // The point lies in the last bin along this axis. The trilinear
    // interpolation uses the iBin+1 neighbour, which would fall outside the
    // axis here, so clamp to the last valid cell (Nu-2) and use a fractional
    // weight of 1 so the upper-edge (last valid) slice is used without reading
    // the next, non-existent slice.
    iBin = Nu - 2;
    fracL = 1.0;
  }

  // Return the bin number and fractional distance of the point from the
  // leftmost bin edge
  binPair binInfo(iBin, fracL);

  return binInfo;
}

Int_t ShipBFieldMap::getMapBin(Int_t iX, Int_t iY, Int_t iZ) {
  // Get the index of the map entry corresponding to the x,y,z bins.
  // Remember that the map is ordered in ascending z, y, then x

  Int_t index = (iX * Ny_ + iY) * Nz_ + iZ;
  if (index < 0) {
    index = 0;
  } else if (index >= N_) {
    index = N_ - 1;
  }

  return index;
}

Float_t ShipBFieldMap::triLinearInterp(Float_t A, Float_t B, Float_t C,
                                       Float_t D, Float_t E, Float_t F,
                                       Float_t G, Float_t H, Float_t xFrac,
                                       Float_t xFrac1, Float_t yFrac,
                                       Float_t yFrac1, Float_t zFrac,
                                       Float_t zFrac1) {
  // Trilinear interpolation of a single component from its eight corner values
  // A..H (bit-for-bit the arithmetic previously performed per axis by
  // BInterCalc).
  // Linear interpolation along x
  const Float_t F00 = A * xFrac1 + B * xFrac;
  const Float_t F10 = C * xFrac1 + D * xFrac;
  const Float_t F01 = E * xFrac1 + F * xFrac;
  const Float_t F11 = G * xFrac1 + H * xFrac;

  // Linear interpolation along y
  const Float_t F0 = F00 * yFrac1 + F10 * yFrac;
  const Float_t F1 = F01 * yFrac1 + F11 * yFrac;

  // Linear interpolation along z
  return F0 * zFrac1 + F1 * zFrac;
}
