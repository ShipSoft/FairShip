#!/usr/bin/env python
"""Script to generate DIS events for muons in Pythia6, and save them to a ROOT file (along with the original muon's soft interactions)."""

import argparse
import logging
import os
import time
from array import array

import ROOT as r
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
PDG = r.TDatabasePDG.Instance()
PDG.AddParticle("C12", "Carbon-12", 12.0, True, 0, 6.0, "nucleus", 1000060120)
PDG.AddParticle("C13", "Carbon-13", 13.003355, True, 0, 6.0, "nucleus", 1000060130)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-f", "--inputFile", help="Input file to use", required=True)
parser.add_argument("-o", "--outputFile", help="Output file to use", required=False, default="muonDis.root")
parser.add_argument(
    "-i",
    "--firstEvent",
    dest="first_mu_event",
    help="First event of muon file to use",
    required=False,
    default=0,
    type=int,
)
parser.add_argument(
    "-n",
    "--nEvents",
    dest="n_events",
    help="Number of muons to generate DIS for",
    required=False,
    default=10,
    type=int,
)
parser.add_argument(
    "-nDISPerMuon",
    "--nDIS",
    help="Number of DIS per muon to generate",
    required=False,
    default=1000,
    type=int,
)

args = parser.parse_args()
n_events = args.n_events
first_mu_event = args.first_mu_event


def rotate(px, py, pz, theta, phi):
    """Rotate the daughter particle momentum to align with respect to the muon's momentum."""
    momentum = r.TVector3(px, py, pz)

    rotation = r.TRotation()
    rotation.RotateY(theta)  # Rotate around the Y-axis
    rotation.RotateZ(phi)  # Rotate around the Z-axis

    # Apply the rotation to the momentum vector
    rotated_momentum = rotation * momentum

    return rotated_momentum.X(), rotated_momentum.Y(), rotated_momentum.Z()


def update_file(filename, final_xsec):
    """Update the DIS cross section of the muon to the converged value from Pythia."""
    file = r.TFile.Open(filename, "read")

    original_tree = file.DIS

    temp_filename = filename + ".tmp"
    temp_file = r.TFile.Open(temp_filename, "recreate")

    updated_tree = original_tree.CloneTree(0)

    for i, event in enumerate(original_tree):
        mu = event.InMuon[0]
        mu[10] = final_xsec[int(first_mu_event + i / args.nDIS)]
        updated_tree.Fill()

    updated_tree.Write("DIS", r.TObject.kOverwrite)
    temp_file.Close()
    file.Close()

    os.remove(filename)
    os.rename(temp_filename, filename)
    logging.info("Muon DIS events successfully updated with converged cross sections.")


headers = [
    "DIS_index",
    "Fix_Target",
    "nParticles in event",
    "nSoftTracks_iMuon",
    "nSBThits_iMuon",
    "nUBThits_iMuon",
    "nLastBitMuonShieldHits_iMuon",
    "cross_sec",
]
Fixtarget = {1: "p+", 0: "n0"}


def inspect_file(filename):
    """Inspect the contents of muonDis file."""
    file = r.TFile.Open(filename, "READ")
    tree = file.DIS

    table_rows = []

    for i, event in enumerate(tree):
        muon = event.InMuon[0]
        isProton = int(muon[9])
        fix_target = Fixtarget.get(isProton, "unknown")
        cross_sec = muon[10]

        nParticles = event.DISParticles.GetEntries()
        nSoftTracks = event.SoftParticles.GetEntries()
        nSBThits = event.muon_vetoPoints.GetEntries()
        nUBThits = event.muon_UpstreamTaggerPoints.GetEntries()
        nLastBitMuonShieldHits = event.muon_lastBitMuonShieldPoints.GetEntries()

        table_rows.append(
            [i, fix_target, nParticles, nSoftTracks, nSBThits, nUBThits, nLastBitMuonShieldHits, cross_sec]
        )

    file.Close()
    logging.info("\n" + tabulate(table_rows, headers=headers, tablefmt="grid"))


def makeMuonDIS():
    """Generate DIS events."""
    final_xsec = {}

    logging.info(f"Opening input file: {args.inputFile}")
    muonFile = r.TFile.Open(args.inputFile, "read")

    try:
        muon_tree = muonFile.MuonAndSoftInteractions
    except Exception as e:
        logging.error(e)
        muonFile.Close()
        exit(1)

    logging.debug(f"Total entries in the tree: {muon_tree.GetEntries()}")
    last_mu_event = min(muon_tree.GetEntries(), first_mu_event + n_events)

    logging.info("Creating output file: ", args.outputFile)

    outputFile = r.TFile.Open(args.outputFile, "recreate")
    output_tree = r.TTree("DIS", "muon DIS")

    iMuon = r.TClonesArray("TVectorD")
    output_tree.Branch("InMuon", iMuon, 32000, -1)

    dPartDIS = r.TClonesArray("TVectorD")
    output_tree.Branch("DISParticles", dPartDIS, 32000, -1)

    dPartSoft = r.TClonesArray("TVectorD")
    output_tree.Branch("SoftParticles", dPartSoft, 32000, -1)

    muon_vetoPoints = r.TClonesArray("vetoPoint")
    output_tree.Branch("muon_vetoPoints", muon_vetoPoints, 32000, -1)

    muon_UpstreamTaggerPoints = r.TClonesArray("UpstreamTaggerPoint")
    output_tree.Branch(
        "muon_UpstreamTaggerPoints", muon_UpstreamTaggerPoints, 32000, -1
    )

    muon_lastBitMuonShieldPoints = r.TClonesArray("lastBitMuonShieldPoint")
    output_tree.Branch(
	"muon_lastBitMuonShieldPoints", muon_lastBitMuonShieldPoints, 32000, -1
    )

    myPythia = r.TPythia6()
    #set process 1=QCD, 2=DY/others
    myPythia.SetMSEL(2)
    #set min hard scale: 2 GeV --->try 1.5 for soft muons ?
    myPythia.SetPARP(2, 2)
    #disable decay for those PDGID
    for kf in [211, 321, 130, 310, 3112, 3122, 3222, 3312, 3322, 3334]:
        kc = myPythia.Pycomp(kf)
        myPythia.SetMDCY(kc, 1, 0)

    seed = int(time.time() % 900000000)
    myPythia.SetMRPY(1, seed)
    #dictionary: pythia beam definition to enable gamma radiations
    mutype = {-13: "gamma/mu+", 13: "gamma/mu-"}
    #for pythia6 output, 11=set to output file. 6=stdout.
    myPythia.SetMSTU(11, 11)
    logging.info(
        f"Processing muon events from {first_mu_event} to {last_mu_event - 1}..."
    )

    nMade = 0

    for k in range(first_mu_event, last_mu_event):
        DIS_table = []  # debug
        cross_sections = []

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
        nmuons = imuondata[9]  # number of muons in the original MuBack event

        p = r.TMath.Sqrt(px**2 + py**2 + pz**2)
        mass = PDG.GetParticle(abs(int(pid))).Mass()
        E = r.TMath.Sqrt(mass**2 + p**2)

        theta = r.TMath.ACos(pz / p)
        #returns phi between -pi and pi
        phi = r.TMath.ATan2(py, px)

        isProton = 1
        xsec = 0

        mu = array(
            "d",
            [
                pid,
                px,
                py,
                pz,
                E,
                x,
                y,
                z,
                w,
                isProton,
                xsec,
                time_muon,
                args.nDIS,
                nmuons,
            ],
        )
        muPart = r.TVectorD(14, mu)
        myPythia.Initialize("FIXT", mutype[pid], "p+", p)  # target = "p+"
        #print summary of initialisation params
        myPythia.Pylist(1)

        for a in range(args.nDIS):
            #half-way through, we change to neutron target with 50-50 : ---> update to real material ??
            if a == args.nDIS // 2:
                myPythia.Initialize("FIXT", mutype[pid], "n0", p)  # target = "n0"
                isProton = 0
                # logging.debug("Switching to neutron interaction")

            dPartDIS.Clear()
            iMuon.Clear()
            muPart[9] = isProton
            iMuon[0] = muPart

            myPythia.GenerateEvent()
            #clean all but final stable particles
            myPythia.Pyedit(1)

            xsec = myPythia.GetPARI(1) #in mb
            muPart[10] = xsec

            ndaugh =  myPythia.GetN()
            dPartDIS.Expand(ndaugh)
            
            #loop over daughters and rotate in muon input direction
            for itrk in range(1, ndaugh + 1):
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
                # dPartDIS.ConstructedAt(nPart).Use(part) #to be adapted later
                dPartDIS[itrk-1] = part

            cross_sections.append(xsec)

            dPartSoft.Clear()
            dPartSoft.Expand(muon_tree.tracks.GetSize())

            for isft, softTrack in enumerate(muon_tree.tracks):
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
                # dPartSoft.ConstructedAt(isft).Use(part) #to be adapted later
                dPartSoft[isft] = part

            muon_vetoPoints.Clear()

            index = 0
            for hit in muon_tree.muon_vetoPoints:
                if muon_vetoPoints.GetSize() == index:
                    muon_vetoPoints.Expand(index + 1)
                hit.SetTrackID(0)  # Set TrackID to match for muon ID for new simulation
                muon_vetoPoints[index] = hit
                index += 1

            muon_UpstreamTaggerPoints.Clear()

            ubt_index = 0
            for hit in muon_tree.muon_UpstreamTaggerPoints:
                if muon_UpstreamTaggerPoints.GetSize() == ubt_index:
                    muon_UpstreamTaggerPoints.Expand(ubt_index + 1)
                hit.SetTrackID(0)  # Set TrackID to match for muon ID for new simulation
                muon_UpstreamTaggerPoints[ubt_index] = hit
                ubt_index += 1

            muon_lastBitMuonShieldPoints.Clear()

            lastBitMuonShieldPoints_index = 0
            for hit in muon_tree.muon_lastBitMuonShieldPoints:
                if muon_lastBitMuonShieldPoints.GetSize() == lastBitMuonShieldPoints_index:
                    muon_lastBitMuonShieldPoints.Expand(lastBitMuonShieldPoints_index + 1)
                hit.SetTrackID(0)  # Set TrackID to match for muon ID for new simulation
                muon_lastBitMuonShieldPoints[lastBitMuonShieldPoints_index] = hit
                lastBitMuonShieldPoints_index += 1

            output_tree.Fill()
            DIS_table.append(
                [
                    a,
                    Fixtarget[isProton],
                    myPythia.GetN(),
                    len(dPartSoft),
                    len(muon_vetoPoints),
                    len(muon_UpstreamTaggerPoints),
                    len(muon_lastBitMuonShieldPoints),
                    xsec,
                ]
            )

        # --> why take the last one ? Why not the average of all nDIS ?? Using cross_sections array 
        final_xsec[k] = xsec

        nMade += 1
        logging.debug(
            f"\nMuon index:{k} \n\tPID = {pid}, weight = {w}, converged_cross_section= {final_xsec[k]}\n\tpx = {px}, py = {py}, pz = {pz}, E = {E},\n\tx = {x}, y = {y}, z = {z}\n\n\tDIS Events Summary\n{tabulate(DIS_table, headers=headers, tablefmt='grid')}"
        )
        if nMade % 10 == 0:
            logging.info(f"Muons processed: {nMade}")

    outputFile.cd()
    output_tree.Write()
    myPythia.SetMSTU(11, 6)
    logging.info(
        f"DIS generated for muons (index {first_mu_event} - {last_mu_event - 1}) , output saved in {args.outputFile}, nDISPerMuon = {args.nDIS}"
    )
    outputFile.Close()
    muonFile.Close()

    #set the same xs for all DIS events of the same muon... why ?
    update_file(args.outputFile, final_xsec)


if __name__ == "__main__":
    makeMuonDIS()
    inspect_file(args.outputFile)
