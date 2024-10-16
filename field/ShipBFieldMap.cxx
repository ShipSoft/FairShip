/*! \class ShipBFieldMap
  \brief Class that defines a (3d) magnetic field map (distances in cm, fields in tesla)

  \author John Back <J.J.Back@warwick.ac.uk>
*/

#include "ShipBFieldMap.h"

#include "TFile.h"
#include "TTree.h"

#include <fstream>
#include <iostream>

ShipBFieldMap::ShipBFieldMap(const std::string& label,
			     const std::string& mapFileName,
			     Float_t xOffset,
			     Float_t yOffset,
			     Float_t zOffset,
			     Float_t phi,
			     Float_t theta,
			     Float_t psi,
			     Float_t scale,
			     Bool_t isSymmetric) :
    TVirtualMagField(label.c_str()),
    fieldMap_(new floatArray()),
    mapFileName_(mapFileName),
    initialised_(kFALSE),
    isCopy_(kFALSE),
    Nx_(0), Ny_(0), Nz_(0), N_(0),
    xMin_(0.0), xMax_(0.0),
    dx_(0.0), xRange_(0.0),
    yMin_(0.0), yMax_(0.0),
    dy_(0.0), yRange_(0.0),
    zMin_(0.0), zMax_(0.0),
    dz_(0.0), zRange_(0.0),
    xOffset_(xOffset),
    yOffset_(yOffset),
    zOffset_(zOffset),
    phi_(phi),
    theta_(theta),
    psi_(psi),
    scale_(scale),
    isSymmetric_(isSymmetric),
    theTrans_(0),
    Tesla_(10.0)
{
    this->initialise();
}

ShipBFieldMap::~ShipBFieldMap()
{
    // Delete the internal vector storing the field map values
    if (fieldMap_ && isCopy_ == kFALSE) {
	delete fieldMap_; fieldMap_ = 0;
    }

    if (theTrans_) {delete theTrans_; theTrans_ = 0;}

}


ShipBFieldMap::ShipBFieldMap(const std::string& newName, const ShipBFieldMap& rhs,
			     Float_t newXOffset, Float_t newYOffset, Float_t newZOffset,
			     Float_t newPhi, Float_t newTheta, Float_t newPsi, Float_t newScale) :
    TVirtualMagField(newName.c_str()),
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
    theTrans_(0),
    Tesla_(10.0)
{
    // Copy constructor with new label and different global offset, which uses
    // the same field map data (pointer) and distance units as the rhs object
    this->initialise();
}

void ShipBFieldMap::Field(const Double_t* position, Double_t* B)
{

    // Set the B field components given the global position co-ordinates

    // Convert the global position into a local one for the volume field.
    // Initialise the local co-ords, which will get overwritten if the
    // co-ordinate transformation exists. For a global field, any local
    // volume transformation is ignored
    Double_t localCoords[3] = {position[0], position[1], position[2]};

    if (theTrans_) {theTrans_->MasterToLocal(position, localCoords);}

    // The local position co-ordinates
    Float_t x = localCoords[0];
    Float_t y = localCoords[1];
    Float_t z = localCoords[2];

    // Now check to see if we have x-y quadrant symmetry (z has no symmetry):
    // Bx is antisymmetric in x and y, By is symmetric and Bz has no symmetry
    // so only Bx can change sign. This can happen if either x < 0 or y < 0:
    // 1. x > 0, y > 0: Bx = Bx
    // 2. x > 0, y < 0: Bx = -Bx
    // 3. x < 0, y > 0: Bx = -Bx
    // 4. x < 0, y < 0: Bx = Bx

    Float_t BxSign(1.0);
    Float_t BzSign = 1;

    if (isSymmetric_) {

      // The field map co-ordinates only contain x > 0 and y > 0, i.e. we
      // are using x-y quadrant symmetry. If the local x or y coordinates
      // are negative we need to change their sign and keep track of the
      // adjusted sign of Bx which we use as a multiplication factor at the end
      if (x < 0.0) {
	x = -x; BxSign *= -1.0;
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
    if (inside == kFALSE) {return;}

    // Find the neighbouring bins for the given point
    binPair xBinInfo = this->getBinInfo(x, ShipBFieldMap::xAxis);
    binPair yBinInfo = this->getBinInfo(y, ShipBFieldMap::yAxis);
    binPair zBinInfo = this->getBinInfo(z, ShipBFieldMap::zAxis);

    Int_t iX = xBinInfo.first;
    Int_t iY = yBinInfo.first;
    Int_t iZ = zBinInfo.first;

    // Check that the bins are valid
    if (iX == -1 || iY == -1 || iZ == -1) {return;}

    // Get the various neighbouring bin entries
    Int_t iX1(iX + 1);
    Int_t iY1(iY + 1);
    Int_t iZ1(iZ + 1);

    binA_ = this->getMapBin(iX, iY, iZ);
    binB_ = this->getMapBin(iX1, iY, iZ);
    binC_ = this->getMapBin(iX, iY1, iZ);
    binD_ = this->getMapBin(iX1, iY1, iZ);
    binE_ = this->getMapBin(iX, iY, iZ1);
    binF_ = this->getMapBin(iX1, iY, iZ1);
    binG_ = this->getMapBin(iX, iY1, iZ1);
    binH_ = this->getMapBin(iX1, iY1, iZ1);

    // Retrieve the fractional bin distances
    xFrac_ = xBinInfo.second;
    yFrac_ = yBinInfo.second;
    zFrac_ = zBinInfo.second;

    // Set the complimentary fractional bin distances
    xFrac1_ = 1.0 - xFrac_;
    yFrac1_ = 1.0 - yFrac_;
    zFrac1_ = 1.0 - zFrac_;

    // Finally get the magnetic field components using trilinear interpolation
    // and scale with the appropriate multiplication factor (default = 1.0)
    B[0] = this->BInterCalc(ShipBFieldMap::xAxis)*scale_*BxSign;
    B[1] = this->BInterCalc(ShipBFieldMap::yAxis)*scale_;
    B[2] = this->BInterCalc(ShipBFieldMap::zAxis) * scale_ * BzSign;

}

void ShipBFieldMap::initialise()
{

    if (initialised_ == kFALSE) {

	if (isCopy_ == kFALSE) {this->readMapFile();}

	// Set the global co-ordinate translation and rotation info
	if (fabs(phi_) > 1e-6 || fabs(theta_) > 1e-6 || fabs(psi_) > 1e-6) {

	    // We have non-zero rotation angles. Create a combined translation and rotation
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

void ShipBFieldMap::readMapFile()
{

    std::cout<<"ShipBFieldMap::readMapFile() creating field "<<this->GetName()
	     <<" using file "<<mapFileName_<<std::endl;

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
	std::cout<<"ShipBFieldMap: could not find the file "<<mapFileName_<<std::endl;
	return;
    }

    // Coordinate ranges
    TTree* rTree = dynamic_cast<TTree*>(theFile->Get("Range"));
    if (!rTree) {
	std::cout<<"ShipBFieldMap: could not find Range tree in "<<mapFileName_<<std::endl;
	return;
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
	// in ascending z,y,x co-ordinate order

	TTree* dTree = dynamic_cast<TTree*>(theFile->Get("Data"));
	if (!dTree) {
	    std::cout<<"ShipBFieldMap: could not find Data tree in "<<mapFileName_<<std::endl;
	    return;
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
	    std::cout<<"Expected "<<N_<<" field map entries but found "<<nEntries<<std::endl;
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
	    std::vector<Float_t> BVector(3);
	    BVector[0] = Bx; BVector[1] = By; BVector[2] = Bz;
	    fieldMap_->push_back(BVector);

	}

    }

    theFile->Close();

}

void ShipBFieldMap::readTextFile() {

    std::ifstream getData(mapFileName_.c_str());

    std::string tmpString("");

    getData >> tmpString >> xMin_ >> xMax_ >> dx_
	    >> yMin_ >> yMax_ >> dy_ >> zMin_ >> zMax_ >> dz_;

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
	    std::vector<Float_t> BVector(3);
	    BVector[0] = Bx; BVector[1] = By; BVector[2] = Bz;
	    fieldMap_->push_back(BVector);

	}

    }

    getData.close();

}

Bool_t ShipBFieldMap::insideRange(Float_t x, Float_t y, Float_t z)
{

    Bool_t inside(kFALSE);

    if (x >= xMin_ && x <= xMax_ && y >= yMin_ &&
	y <= yMax_ && z >= zMin_ && z <= zMax_) {inside = kTRUE;}

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
	Nx_ = static_cast<Int_t>(((xMax_ - xMin_)/dx_) + 1.5);
    }
    if (dy_ > 0.0) {
	Ny_ = static_cast<Int_t>(((yMax_ - yMin_)/dy_) + 1.5);
    }
    if (dz_ > 0.0) {
	Nz_ = static_cast<Int_t>(((zMax_ - zMin_)/dz_) + 1.5);
    }

    N_ = Nx_*Ny_*Nz_;

    std::cout<<"x limits: "<<xMin_<<", "<<xMax_<<", dx = "<<dx_<<std::endl;
    std::cout<<"y limits: "<<yMin_<<", "<<yMax_<<", dy = "<<dy_<<std::endl;
    std::cout<<"z limits: "<<zMin_<<", "<<zMax_<<", dz = "<<dz_<<std::endl;

    std::cout<<"Offsets: x = "<<xOffset_<<", y = "<<yOffset_<<", z = "<<zOffset_<<std::endl;
    std::cout<<"Angles : phi = "<<phi_<<", theta = "<<theta_<<", psi = "<<psi_<<std::endl;

    std::cout<<"Total number of bins = "<<N_
	     <<"; Nx = "<<Nx_<<", Ny = "<<Ny_<<", Nz = "<<Nz_<<std::endl;

}


ShipBFieldMap::binPair ShipBFieldMap::getBinInfo(Float_t u, ShipBFieldMap::CoordAxis theAxis)
{

    Float_t du(0.0), uMin(0.0), Nu(0);

    if (theAxis == ShipBFieldMap::xAxis) {
	du = dx_; uMin = xMin_; Nu = Nx_;
    } else if (theAxis == ShipBFieldMap::yAxis) {
	du = dy_; uMin = yMin_; Nu = Ny_;
    } else if (theAxis == ShipBFieldMap::zAxis) {
	du = dz_; uMin = zMin_; Nu = Nz_;
    }

    Int_t iBin(-1);
    Float_t fracL(0.0);

    if (du > 1e-10) {

	// Get the number of fractional bin widths the point is from the first volume bin
	Float_t dist = (u - uMin)/du;
	// Get the integer equivalent of this distance, which is the bin number
	iBin = static_cast<Int_t>(dist);
	// Get the actual fractional distance of the point from the leftmost bin edge
	fracL = (dist - iBin*1.0);

    }

    // Check that the bin number is valid
    if (iBin < 0 || iBin >= Nu) {
	iBin = -1; fracL = 0.0;
    }

    // Return the bin number and fractional distance of the point from the leftmost bin edge
    binPair binInfo(iBin, fracL);

    return binInfo;

}

Int_t ShipBFieldMap::getMapBin(Int_t iX, Int_t iY, Int_t iZ)
{

    // Get the index of the map entry corresponding to the x,y,z bins.
    // Remember that the map is ordered in ascending z, y, then x

    Int_t index = (iX*Ny_ + iY)*Nz_ + iZ;
    if (index < 0) {
	index = 0;
    } else if (index >= N_) {
	index = N_-1;
    }

    return index;

}

Float_t ShipBFieldMap::BInterCalc(CoordAxis theAxis)
{

    // Find the magnetic field component along theAxis using trilinear
    // interpolation based on the current position and neighbouring bins
    Float_t result(0.0);

    Int_t iAxis(0);

    if (theAxis == CoordAxis::yAxis) {
	iAxis = 1;
    } else if (theAxis == CoordAxis::zAxis) {
	iAxis = 2;
    }

    if (fieldMap_) {

	// Get the field component values for the neighbouring bins
	Float_t A = (*fieldMap_)[binA_][iAxis];
	Float_t B = (*fieldMap_)[binB_][iAxis];
	Float_t C = (*fieldMap_)[binC_][iAxis];
	Float_t D = (*fieldMap_)[binD_][iAxis];
	Float_t E = (*fieldMap_)[binE_][iAxis];
	Float_t F = (*fieldMap_)[binF_][iAxis];
	Float_t G = (*fieldMap_)[binG_][iAxis];
	Float_t H = (*fieldMap_)[binH_][iAxis];

	// Perform linear interpolation along x
	Float_t F00 = A*xFrac1_ + B*xFrac_;
	Float_t F10 = C*xFrac1_ + D*xFrac_;
	Float_t F01 = E*xFrac1_ + F*xFrac_;
	Float_t F11 = G*xFrac1_ + H*xFrac_;

	// Linear interpolation along y
	Float_t F0 = F00*yFrac1_ + F10*yFrac_;
	Float_t F1 = F01*yFrac1_ + F11*yFrac_;

	// Linear interpolation along z
	result = F0*zFrac1_ + F1*zFrac_;

    }

    return result;

}
