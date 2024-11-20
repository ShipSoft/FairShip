#!/usr/bin/env python
"""Script to generate DIS events for muons in Pythia6, and sve to a ROOT file (along with the original muon's soft interactions)."""

import argparse
import logging
import time
from array import array

import ROOT as r

logging.basicConfig(level=logging.INFO)
PDG = r.TDatabasePDG.Instance()


def rotate(px, py, pz, theta, phi):
    """Rotate the daughter particle momentum to align with respect to the muon's momentum."""
    momentum = r.TVector3(px, py, pz)

    rotation = r.TRotation()
    rotation.RotateY(theta)  # Rotate around the Y-axis
    rotation.RotateZ(phi)  # Rotate around the Z-axis

    # Apply the rotation to the momentum vector
    rotated_momentum = rotation * momentum

    return rotated_momentum.X(), rotated_momentum.Y(), rotated_momentum.Z()


def makeMuonDIS():
    """Generate DIS events."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--inputFile", help="Input file to use", required=True)
    parser.add_argument(
        "-nJob", "--nJob", type=int, help="Process ID, gives muon index", required=True
    )
    parser.add_argument(
        "-nPerJobs",
        "--nPerJobs",
        type=int,
        help="The number of muons per file",
        required=True,
    )
    parser.add_argument(
        "-nDISPerMuon",
        "--nDIS",
        type=int,
        help="Number of DIS per muon to generate",
        required=True,
    )

    args = parser.parse_args()

    logging.info(f"Opening input file: {args.inputFile}")
    muonFile = r.TFile.Open(args.inputFile, "read")

    try:
        muon_tree = muonFile.MuonAndSoftInteractions
    except Exception as e:
        print(f"Error: {e}")
        muonFile.Close()
        exit(1)

    nPerJob = args.nPerJobs  # number of muons handled by the python script
    nStart = args.nPerJobs * args.nJob
    logging.debug(f"Total entries in the tree: {muon_tree.GetEntries()}")
    nEnd = min(muon_tree.GetEntries(), nStart + nPerJob)

    logging.info(f"Creating output file: muonDis_{args.nJob}.root")

    outputFile = r.TFile.Open(f"muonDis_{args.nJob}.root", "recreate")
    output_tree = r.TTree("DIS", "muon DIS")

    iMuon = r.TClonesArray("TVectorD")
    output_tree.Branch("InMuon", iMuon, 32000, -1)

    dPartDIS = r.TClonesArray("TVectorD")
    output_tree.Branch("DISParticles", dPartDIS, 32000, -1)

    dPartSoft = r.TClonesArray("TVectorD")
    output_tree.Branch("SoftParticles", dPartSoft, 32000, -1)

    muon_vetoPoints = r.TClonesArray("vetoPoint")
    output_tree.Branch("muon_vetoPoints", muon_vetoPoints, 32000, -1)

    myPythia = r.TPythia6()
    myPythia.SetMSEL(2)
    myPythia.SetPARP(2, 2)
    for kf in [211, 321, 130, 310, 3112, 3122, 3222, 3312, 3322, 3334]:
        kc = myPythia.Pycomp(kf)
        myPythia.SetMDCY(kc, 1, 0)

    seed = int(time.time() % 900000000)
    myPythia.SetMRPY(1, seed)
    mutype = {-13: "gamma/mu+", 13: "gamma/mu-"}

    myPythia.SetMSTU(11, 11)
    logging.info(f"Processing events from {nStart} to {nEnd-1}...")

    nMade = 0

    for k in range(nStart, nEnd):
        muon_tree.GetEvent(k)

        imuondata = muon_tree.imuondata

        pid = imuondata[0]
        px = imuondata[1]
        py = imuondata[2]
        pz = imuondata[3]
        x = imuondata[4]
        y = imuondata[5]
        z = imuondata[6]
        w = imuondata[7]
        time_muon = imuondata[8]

        p = r.TMath.Sqrt(px**2 + py**2 + pz**2)
        mass = PDG.GetParticle(abs(int(pid))).Mass()
        E = r.TMath.Sqrt(mass**2 + p**2)

        theta = r.TMath.ACos(pz / p)
        phi = r.TMath.ATan2(py, px)

        logging.debug(
            f"\n\tMuon index:{k} \n\tPID = {pid}, weight = {w} \n\tpx = {px}, py = {py}, pz = {pz}, E = {E},\n\tx = {x}, y = {y}, z = {z}\n"
        )

        isProton = 1
        xsec = 0

        mu = array("d", [pid, px, py, pz, E, x, y, z, w, isProton, xsec, time_muon])
        muPart = r.TVectorD(12, mu)
        myPythia.Initialize("FIXT", mutype[pid], "p+", p)  # target = "p+"
        myPythia.Pylist(1)

        for a in range(args.nDIS):
            if a == args.nDIS // 2:
                myPythia.Initialize("FIXT", mutype[pid], "n0", p)  # target = "n0"
                isProton = 0
                logging.debug("Switching to neutron interaction")

            dPartDIS.Clear()
            iMuon.Clear()
            muPart[9] = isProton
            iMuon[0] = muPart
            myPythia.GenerateEvent()
            myPythia.Pyedit(1)
            logging.debug(
                f"DIS Event {a} generated, number of particles: {myPythia.GetN()}"
            )

            for itrk in range(1, myPythia.GetN() + 1):
                xsec = myPythia.GetPARI(1)
                muPart[10] = xsec
                did = myPythia.GetK(itrk, 2)
                dpx, dpy, dpz = rotate(
                    myPythia.GetP(itrk, 1),
                    myPythia.GetP(itrk, 2),
                    myPythia.GetP(itrk, 3),
                    theta,
                    phi,
                )
                psq = dpx**2 + dpy**2 + dpz**2
                masssq = PDG.GetParticle(did).Mass() ** 2
                E = r.TMath.Sqrt(masssq + psq)
                m = array("d", [did, dpx, dpy, dpz, E])
                part = r.TVectorD(5, m)
                nPart = dPartDIS.GetEntries()
                if dPartDIS.GetSize() == nPart:
                    dPartDIS.Expand(nPart + 10)
                # dPartDIS.ConstructedAt(nPart).Use(part) #to be adapted later
                dPartDIS[nPart] = part
                if itrk == 1:
                    with open(f"sigmadata_{args.nJob}.txt", "a") as fcross:
                        fcross.write(f"{xsec}\n")

            dPartSoft.Clear()

            for softTrack in muon_tree.tracks:
                did = softTrack.GetPdgCode()
                dpx = softTrack.GetPx()
                dpy = softTrack.GetPy()
                dpz = softTrack.GetPz()

                psq = dpx**2 + dpy**2 + dpz**2
                masssq = PDG.GetParticle(did).Mass() ** 2
                E = r.TMath.Sqrt(masssq + psq)

                softx = softTrack.GetStartX()
                softy = softTrack.GetStartY()
                softz = softTrack.GetStartZ()
                time_ = softTrack.GetStartT()

                m = array("d", [did, dpx, dpy, dpz, E, softx, softy, softz, time_])

                part = r.TVectorD(9, m)
                nPart = dPartSoft.GetEntries()
                if dPartSoft.GetSize() == nPart:
                    dPartSoft.Expand(nPart + 10)
                # dPartSoft.ConstructedAt(nPart).Use(part) #to be adapted later
                dPartSoft[nPart] = part

            muon_vetoPoints.Clear()

            index = 0
            for hit in muon_tree.muon_vetoPoints:
                if muon_vetoPoints.GetSize() == index:
                    muon_vetoPoints.Expand(index + 1)
                hit.SetTrackID(0)  # Set TrackID to match for muon ID for new simulation
                muon_vetoPoints[index] = hit
                index += 1

            output_tree.Fill()

        nMade += 1

        if nMade % 10 == 0:
            logging.info(f"Muons processed: {nMade}")

    outputFile.cd()
    output_tree.Write()
    myPythia.SetMSTU(11, 6)
    logging.info(
        f"DIS generated for muons (index {nStart} - {nEnd-1}) , output saved in muonDis_{args.nJob}.root, nDISPerMuon = {args.nDIS}"
    )


if __name__ == "__main__":
    makeMuonDIS()
