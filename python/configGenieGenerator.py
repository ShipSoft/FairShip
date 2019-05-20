import ROOT
# configure the GenieGenerator
def config(GenieGen):
 fGeo = ROOT.gGeoManager
 top = fGeo.GetTopVolume()
# positions for nu events inside the nutau detector volume
 muDetector      = top.FindNode("volNuTauMudet_1")
 muDetectorTrans = muSpectrometer.GetMatrix().GetTranslation()
# upper and lower yokes:
# volFeYoke_1, volFeYoke_2, volFeYoke1_1  (in UpYoke) and  volFeYoke_3, volFeYoke_4, volFeYoke1_1 (in LowYoke).
 yokes = ["volUpYoke_1","volLowYoke_1","volArm2Mudet_1"]
 vols  = ["volFeYoke_1", "volFeYoke_2", "volFeYoke1_1","volFeYoke_3", "volFeYoke_4","volIron_12","volIron_23"]
 dVec = {}
 box  = {}
 for anode in muSpectrometer.GetNodes(): 
  if anode.GetName() in yokes:
    aTrans = anode.GetMatrix().GetTranslation()
    for bnode in anode.GetNodes():      
      if bnode.GetName() in vols:
          bTrans = bnode.GetMatrix().GetTranslation()
          nm = anode.GetName()+'/'+bnode.GetName() 
          dVec[nm] = ROOT.TVector3()
          x = []
          for k in range(3): x.append(aTrans[k]+bTrans[k]+muSpectrometerTrans[k])
          dVec[nm].SetXYZ(x[0],x[1],x[2])
          sbnode = bnode.GetVolume().GetShape()
          box[nm]=ROOT.TVector3(sbnode.GetDX(),sbnode.GetDY(),sbnode.GetDZ())
          print "Debug muonSpectro ",nm,dVec[nm],box[nm]
 length = dVec["volArm2Mudet_1/volIron_23"].Z()-dVec["volArm2Mudet_1/volIron_12"].Z()
 zpos   = ( dVec["volArm2Mudet_1/volIron_12"].Z()+dVec["volArm2Mudet_1/volIron_23"].Z() )/2.
 box["volArm2Mudet_1/volIron_12-23"]  = ROOT.TVector3(box["volArm2Mudet_1/volIron_12"].X(),box["volArm2Mudet_1/volIron_12"].Y(),length)
 dVec["volArm2Mudet_1/volIron_12-23"] = ROOT.TVector3(0,0,zpos)
 rc = box.pop("volArm2Mudet_1/volIron_23")
 rc = box.pop("volArm2Mudet_1/volIron_12")
 if GenieGen=='debug':
  for aVol in box: 
   print '%50s %6.2F %6.2F %6.2F %5.2F %7.2F %7.2F '%(aVol,box[aVol].X(),box[aVol].Y(),box[aVol].Z(),dVec[aVol].X(),dVec[aVol].Y(),dVec[aVol].Z()) 
 else:
  for aVol in box:
   GenieGen.AddBox(dVec[aVol],box[aVol])
