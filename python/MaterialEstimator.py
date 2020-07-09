import ROOT
from array import array
def MeanMaterialBudget(start, end):
  #
  # Calculate mean material budget and material properties between
  #    the points "start" and "end".
  #
  # "mparam" - parameters used for the energy and multiple scattering
  #  corrections:
  #
  # mparam[0] - mean density: sum(x_i*rho_i)/sum(x_i) [g/cm3]
  # mparam[1] - equivalent rad length fraction: sum(x_i/X0_i) [adimensional]
  # mparam[2] - mean A: sum(x_i*A_i)/sum(x_i) [adimensional]
  # mparam[3] - mean Z: sum(x_i*Z_i)/sum(x_i) [adimensional]
  # mparam[4] - length: sum(x_i) [cm]
  # mparam[5] - Z/A mean: sum(x_i*Z_i/A_i)/sum(x_i) [adimensional]
  # mparam[6] - number of boundary crosses
  # mparam[7] - maximum density encountered (g/cm^3)
  # mparam[8] - equivalent interaction length fraction: sum(x_i/I0_i) [adimensional]
  # mparam[9] - maximum cross section encountered (mbarn)
  #
  #  Origin:  Marian Ivanov, Marian.Ivanov@cern.ch
  #
  #  Corrections and improvements by
  #        Andrea Dainese, Andrea.Dainese@lnl.infn.it,
  #        Andrei Gheata,  Andrei.Gheata@cern.ch
  #        Thomas Ruf,  Thomas.Ruf@cern.ch
  #
  mparam = [0,0,0,0,0,0,0,0,0,0]
  #
  bparam = array('d',[0,0,0,0,0,0,0]) # total parameters
  lparam = array('d',[0,0,0,0,0,0,0]) # local parameters
  mbarn = 1E-3*1E-24*ROOT.TMath.Na() # cm^2 * Avogadro

  if not ROOT.gGeoManager:
    print "no gGeoManager"
    return 0.

  Dir    = array('d',[0,0,0])
  length = ROOT.TMath.Sqrt((end[0]-start[0])*(end[0]-start[0])+
                       (end[1]-start[1])*(end[1]-start[1])+
                       (end[2]-start[2])*(end[2]-start[2]))
  mparam[4]=length
  if length<ROOT.TGeoShape.Tolerance(): 
     print "length smaller than tolerance"
     return mparam
  invlen = 1./length
  Dir[0] = (end[0]-start[0])*invlen
  Dir[1] = (end[1]-start[1])*invlen
  Dir[2] = (end[2]-start[2])*invlen

  # Initialize start point and direction
  startnode = ROOT.gGeoManager.InitTrack(start[0],start[1],start[2], Dir[0],Dir[1],Dir[2])
  if not startnode:
    print "start point out of geometry: x %5.3F, y %5.3F, z %5.3F"%(start[0],start[1],start[2])
    return mparam
  
  material = startnode.GetVolume().GetMedium().GetMaterial()
  lparam[0]   = material.GetDensity()
  if lparam[0] > mparam[7]: mparam[7]=lparam[0]
  lparam[1]   = material.GetRadLen()
  lparam[2]   = material.GetA()
  lparam[3]   = material.GetZ()
  lparam[4]   = length
  lparam[5]   = lparam[3]/lparam[2]
  lparam[6]   = material.GetIntLen()
  n = lparam[0]/lparam[2]
  sigma = 1./(n*lparam[6])/mbarn
  if sigma > mparam[9]: mparam[9]=sigma
  if material.IsMixture():
    mixture = material
    lparam[5] = 0
    Sum = 0
    for iel in range(mixture.GetNelements()):
      Sum  += mixture.GetWmixt()[iel]
      lparam[5]+= mixture.GetZmixt()[iel]*mixture.GetWmixt()[iel]/mixture.GetAmixt()[iel]
    lparam[5] = lparam[5]/Sum

  # Locate next boundary within length without computing safety.
  # Propagate either with length (if no boundary found) or just cross boundary
  ROOT.gGeoManager.FindNextBoundaryAndStep(length, ROOT.kFALSE)
  step = 0.0 # Step made
  snext = ROOT.gGeoManager.GetStep()
  # If no boundary within proposed length, return current density
  if not ROOT.gGeoManager.IsOnBoundary():
    mparam[0] = lparam[0]
    mparam[1] = lparam[4]/lparam[1]
    mparam[2] = lparam[2]
    mparam[3] = lparam[3]
    mparam[4] = lparam[4]
    mparam[8] = lparam[4]/lparam[6]
    return mparam
  # Try to cross the boundary and see what is next
  nzero = 0
  while length>ROOT.TGeoShape.Tolerance():
    currentnode = ROOT.gGeoManager.GetCurrentNode()
    if snext<2.*ROOT.TGeoShape.Tolerance(): nzero+=1
    else: nzero = 0
    if nzero>3:
      # This means navigation has problems on one boundary
      step = 0.1
      print "Cannot cross boundary"
      mparam[0] = bparam[0]/step
      mparam[1] = bparam[1]
      mparam[2] = bparam[2]/step
      mparam[3] = bparam[3]/step
      mparam[5] = bparam[5]/step
      mparam[8] = bparam[6]
      mparam[4] = step
      mparam[0] = 0.             # if crash of navigation take mean density 0
      mparam[1] = 1000000        # and infinite rad length
      return mparam
    
    mparam[6]+=1.
    step += snext
    bparam[1]    += snext/lparam[1]
    bparam[2]    += snext*lparam[2]
    bparam[3]    += snext*lparam[3]
    bparam[5]    += snext*lparam[5]
    bparam[6]    += snext/lparam[6]
    bparam[0]    += snext*lparam[0]

    if snext>=length: break
    if not currentnode: break
    length -= snext
    material = currentnode.GetVolume().GetMedium().GetMaterial()
    lparam[0] = material.GetDensity()
    if lparam[0] > mparam[7]: mparam[7]=lparam[0]
    lparam[1]  = material.GetRadLen()
    lparam[2]  = material.GetA()
    lparam[3]  = material.GetZ()
    lparam[5]   = lparam[3]/lparam[2]
    lparam[6]   = material.GetIntLen()
    n = lparam[0]/lparam[2]
    sigma = 1./(n*lparam[6])/mbarn
    if sigma > mparam[9]: mparam[9]=sigma
    if material.IsMixture():
      mixture = material
      lparam[5]=0
      Sum =0
      for iel in range(mixture.GetNelements()):
        Sum+= mixture.GetWmixt()[iel]
        lparam[5]+= mixture.GetZmixt()[iel]*mixture.GetWmixt()[iel]/mixture.GetAmixt()[iel]
      lparam[5]=lparam[5]/Sum
    ROOT.gGeoManager.FindNextBoundaryAndStep(length, ROOT.kFALSE)
    snext = ROOT.gGeoManager.GetStep()
  
  mparam[0] = bparam[0]/step
  mparam[1] = bparam[1]
  mparam[2] = bparam[2]/step
  mparam[3] = bparam[3]/step
  mparam[5] = bparam[5]/step
  mparam[8] = bparam[6]
  return mparam
