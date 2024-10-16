import ROOT as r
import time
import argparse
from array import array

# Dictionary to store mass squared values
masssq = {}
PDG = r.TDatabasePDG.Instance()

def getMasssq(pid):
    """Retrieve mass squared of a particle by its PDG ID."""
    apid = abs(int(pid))
    if apid not in masssq:
        masssq[apid] = PDG.GetParticle(apid).Mass()**2
    return masssq[apid]

def rotate(ctheta, stheta, cphi, sphi, px, py, pz):
    """Rotate particle momentum components."""
    # Rotate around y-axis
    px1 = ctheta * px + stheta * pz
    pzr = -stheta * px + ctheta * pz
    # Rotate around z-axis
    pxr = cphi * px1 - sphi * py
    pyr = sphi * px1 + cphi * py
    return pxr, pyr, pzr

def makeMuonDIS():
    """Main function to generate DIS events."""
    parser = argparse.ArgumentParser(description='Script to generate DIS events')

    parser.add_argument('-f', '--inputFile', help='Input file to use', required=True)
    parser.add_argument('-nJob', '--nJob', type=int, help='Process ID, gives muon index', required=True)
    parser.add_argument('-nPerJobs', '--nPerJobs', type=int, help='The number of muons per file', required=False)
    parser.add_argument('-nDISPerMuon', '--nDIS', type=int, default=10000, help='Number of DIS per muon to generate')

    args = parser.parse_args()

    print(f"Opening input file: {args.inputFile}")
    muonIn = r.TFile.Open(args.inputFile, 'read')
    sTree = muonIn.Get('MuonAndSoftInteractions')
    

    nPerJob = args.nPerJobs #number of muons handled by the python script
    nStart = args.nPerJobs*args.nJob
    print(f"Total entries in the tree: {sTree.GetEntries()}")
    nEnd = min(sTree.GetEntries(), nStart + nPerJob)
    
    print(f"Creating output file: muonDis_{args.nJob}.root")
    fout = r.TFile(f'muonDis_{args.nJob}.root', 'recreate')
    dTree = r.TTree('DIS', 'muon DIS')

    
    iMuon = r.TClonesArray("TVectorD")
    dTree.Branch("InMuon", iMuon, 32000, -1)

    dPartDIS = r.TClonesArray("TVectorD")
    dTree.Branch("DISParticles", dPartDIS, 32000, -1)

    dPartSoft = r.TClonesArray("TVectorD")
    dTree.Branch("SoftParticles", dPartSoft, 32000, -1)

    muon_vetoPoints    = r.TClonesArray("vetoPoint")
    dTree.Branch('muon_vetoPoints', muon_vetoPoints, 32000, -1)

    myPythia = r.TPythia6()
    myPythia.SetMSEL(2)
    myPythia.SetPARP(2, 2)
    for kf in [211, 321, 130, 310, 3112, 3122, 3222, 3312, 3322, 3334]:
        kc = myPythia.Pycomp(kf)
        myPythia.SetMDCY(kc, 1, 0)

    R = int(time.time() % 900000000)
    myPythia.SetMRPY(1, R)
    mutype = {-13: 'gamma/mu+', 13: 'gamma/mu-'}

    myPythia.SetMSTU(11, 11)
    print(f"Processing events from {nStart} to {nEnd}...")

    nMade = 0
    
    print(nStart, nEnd)
    
    for k in range(nStart, nEnd):
        
        rc = sTree.GetEvent(k)

        imuondata = sTree.imuondata
        
        pid = imuondata[0]
        px = imuondata[1]
        py = imuondata[2]
        pz = imuondata[3]
        x = imuondata[4]
        y = imuondata[5]
        z = imuondata[6]
        w = imuondata[7]
        time_muon=imuondata[8]
        
        p = r.TMath.Sqrt(px ** 2 + py ** 2 + pz ** 2)
        E = r.TMath.Sqrt(getMasssq(pid) + p ** 2)
        theta = r.TMath.ACos(pz / p)
        phi = r.TMath.ATan2(py, px)
        ctheta, stheta = r.TMath.Cos(theta), r.TMath.Sin(theta)
        cphi, sphi = r.TMath.Cos(phi), r.TMath.Sin(phi)

        #print(f"Muon: PID={pid}, px={px}, py={py}, pz={pz}, E={E}, x={x}, y={y}, z={z}, w={w}")
        
        isProton = 1
        xsec = 0

        mu = array('d', [pid, px, py, pz, E, x, y, z, w, isProton, xsec,time_muon])
        muPart = r.TVectorD(12, mu)
        myPythia.Initialize('FIXT', mutype[pid], 'p+', p)
        myPythia.Pylist(1)
        target='p+'
        
        for a in range(args.nDIS):
            if a == args.nDIS // 2:
                myPythia.Initialize('FIXT', mutype[pid], 'n0', p)
                isProton = 0
                target='n0'
                print(f"Switching to neutron interaction")

            dPartDIS.Clear()
            iMuon.Clear()
            muPart[9] = isProton
            iMuon[0] = muPart
            myPythia.GenerateEvent()
            myPythia.Pyedit(1)
            print(f"Event {a} generated, number of particles: {myPythia.GetN()}")

            
            for itrk in range(1, myPythia.GetN() + 1):
                xsec = myPythia.GetPARI(1)
                muPart[10] = xsec
                did = myPythia.GetK(itrk, 2)
                dpx, dpy, dpz = rotate(ctheta, stheta, cphi, sphi, myPythia.GetP(itrk, 1), myPythia.GetP(itrk, 2), myPythia.GetP(itrk, 3))
                psq = dpx ** 2 + dpy ** 2 + dpz ** 2
                E = r.TMath.Sqrt(getMasssq(did) + psq)
                m = array('d', [did, dpx, dpy, dpz, E])
                part = r.TVectorD(5, m)
                nPart = dPartDIS.GetEntries()
                if dPartDIS.GetSize() == nPart:
                    dPartDIS.Expand(nPart + 10)
                dPartDIS[nPart] = part
                if itrk == 1:
                    with open(f'sigmadata_{args.nJob}.txt', "a") as fcross:
                        fcross.write(f"{xsec}\n")
            
            
            dPartSoft.Clear()
            
            softTracks = sTree.tracks

            for itrk in range(softTracks.GetEntries()):
                
                softTrack = softTracks[itrk]
                            
                
                did = softTrack.GetPdgCode()
                dpx = softTrack.GetPx()
                dpy = softTrack.GetPy()
                dpz = softTrack.GetPz()
                
                psq = dpx ** 2 + dpy ** 2 + dpz ** 2
                E = r.TMath.Sqrt(getMasssq(did) + psq)
                
                softx = softTrack.GetStartX()
                softy = softTrack.GetStartY()
                softz = softTrack.GetStartZ()
                time_ = softTrack.GetStartT()
                
                m = array('d', [did, dpx, dpy, dpz, E,softx,softy,softz,time_])
                
                part = r.TVectorD(9, m)
                nPart = dPartSoft.GetEntries()
                if dPartSoft.GetSize() == nPart:
                    dPartSoft.Expand(nPart + 10)
                dPartSoft[nPart] = part
            
            muon_vetoPoints.Clear()
            index=0

            for hit in sTree.muon_vetoPoints:
                if muon_vetoPoints.GetSize() == index:
                    muon_vetoPoints.Expand(index+1)
                muon_vetoPoints[index] = hit
                index+=1
            
            dTree.Fill()
        
        nMade += 1
        
        if nMade % 10 == 0:
            print(f"Muons processed: {nMade}")


    fout.cd()
    dTree.Write()
    myPythia.SetMSTU(11, 6)
    print(f"Created DIS for  saved in muonDis_{args.nJob}.root, muon event index from {nStart} - {nEnd} , nDISPerMuon {args.nDIS}")

if __name__ == '__main__':
    makeMuonDIS()
