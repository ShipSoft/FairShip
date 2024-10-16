import ROOT as r
import os
import argparse
import math
from array import array
from ShipGeoConfig import ConfigRegistry
import shipunit as u

r.PyConfig.IgnoreCommandLineOptions = True

# Histogram
hPmuon = r.TH1F('hPmuon', 'Momentum of muons hitting the SBT;P [GeV];Entries', 400, 0., 400)

# Argument parser
parser = argparse.ArgumentParser(description='Script to collect muons hitting the Tracking Station')
parser.add_argument('-o', '--outputfile', default='muonsProduction_wsoft_Tr.root')
parser.add_argument("-p", dest="path", help="path to muon background files", required=True)
parser.add_argument('-test', dest="testing_code", help="Run Test", action="store_true")
args = parser.parse_args()

# Variables
ev = 0
evs = [0, 0, 0]
processed_events = set()


if args.testing_code: 
    print("test code, output file name overwritten as: muonsProduction_wsoft_Tr_test.root")
    args.outputfile='muonsProduction_wsoft_Tr_test.root'
    selectedmuons='SelectedMuonsTr_test.txt'
else:
    selectedmuons='SelectedMuonsTr.txt'

# Output file and tree setup
output_file = r.TFile(args.outputfile, 'recreate')
output_tree = r.TTree('MuonAndSoftInteractions', 'Muon information and soft interaction tracks')

imuondata = r.TVectorD(9)  # 9 values: pid, px, py, pz, x, y, z, weight,time_of_hit
output_tree.Branch('imuondata', imuondata)

track_array = r.TObjArray()
output_tree.Branch('tracks', track_array)

muon_vetoPoints    = r.TClonesArray("vetoPoint")
output_tree.Branch('muon_vetoPoints', muon_vetoPoints)

path = args.path

fsel = open(selectedmuons, "w")

# Process each input file
for inputFile in os.listdir(path):
    print(inputFile)
    if args.testing_code and evs[2]>=5:
        break

    f = r.TFile.Open(os.path.join(path, inputFile), 'read')
    try:
        tree = f.cbmsim
    except Exception as e:
        print(f"Error: {e}")
        continue

    for event in tree:
        
        ev += 1
        
        #saving soft tracks
        track_array.Clear()
        muon_id = next((itrk for itrk in range(event.MCTrack.GetEntries()) if abs(event.MCTrack[itrk].GetPdgCode()) == 13), None)
        for track in event.MCTrack:
            if track.GetMotherId()==muon_id and (not track.GetProcName().Data() =='Muon nuclear interaction' ):
                track_array.Add(track)
                
        #saving the incoming muon's veto response
        index=0
        muon_vetoPoints.Clear()
        for hit in event.vetoPoint:
            
            detID = hit.GetDetectorID()
            pid = hit.PdgCode()
            if 1000 < detID < 999999 and abs(pid) == 13:
                if muon_vetoPoints.GetSize() == index:
                    muon_vetoPoints.Expand(index+1)
                muon_vetoPoints[index] = hit
                index+=1

        strawDic, trackDic = [], []

        # Process straw tube hits
        for strawHit in event.strawtubesPoint:
            P = r.TMath.Sqrt(strawHit.GetPx() ** 2 + strawHit.GetPy() ** 2 + strawHit.GetPz() ** 2)
            if P > 3:
                detIDmuonS = strawHit.GetDetectorID() // 10000000
                if abs(strawHit.PdgCode()) == 13 and detIDmuonS == 1:
                    if strawHit.GetTrackID() not in strawDic:
                        strawDic.append(strawHit.GetTrackID())
                        evs[0] += 1
                        if evs[0] % 100 == 0:
                            print(f"evs0: {evs[0]}")

        # Process vetoPoint hits
        for hit in event.vetoPoint:
            detID = hit.GetDetectorID()
            pid = hit.PdgCode()
            trackID = hit.GetTrackID()
            if 1000 < detID < 999999 and abs(pid) == 13:
                if trackID not in trackDic:
                    trackDic.append(trackID)
                    evs[1] += 1
                    if evs[1] % 100 == 0:
                        print(f"evs1: {evs[1]}")

        # Check for muons hitting Tr but not SBT and only save them
        for m in strawDic:
            if m not in trackDic:
                for Hit in event.strawtubesPoint:
                    if m == Hit.GetTrackID() and ev not in processed_events:
                        processed_events.add(ev)
                        evs[2] += 1
                        P = r.TMath.Sqrt(Hit.GetPx() ** 2 + Hit.GetPy() ** 2 + Hit.GetPz() ** 2)
                        weight = tree.MCTrack[m].GetWeight()
                        hPmuon.Fill(P, weight)

                        # Fill imuondata
                        imuondata[0] = float(Hit.PdgCode())
                        imuondata[1] = float(Hit.GetPx() / u.GeV)
                        imuondata[2] = float(Hit.GetPy() / u.GeV)
                        imuondata[3] = float(Hit.GetPz() / u.GeV)
                        imuondata[4] = float(Hit.GetX() / u.m)
                        imuondata[5] = float(Hit.GetY() / u.m)
                        imuondata[6] = float(Hit.GetZ() / u.m)
                        imuondata[7] = float(weight)
                        imuondata[8] = float(hit.GetTime())

                        output_tree.Fill()

                        fsel.write(f"{Hit.PdgCode()} {Hit.GetPx() / u.GeV} {Hit.GetPy() / u.GeV} "
                                   f"{Hit.GetPz() / u.GeV} {Hit.GetX() / u.m} {Hit.GetY() / u.m} "
                                   f"{Hit.GetZ() / u.m} {weight}\n")

output_file.cd()
output_tree.Write()
hPmuon.Write()
output_file.Close()
print("Finish:", evs)
fsel.close()


print("------------------------------------------------------file saved, reading",args.outputfile, " now----------------------------------------------------------------")


file = r.TFile(args.outputfile, 'read')
if not file or file.IsZombie():
    print(f"Failed to open file ")
    exit(1)

tree = file.Get("MuonAndSoftInteractions")
if not tree:
    print(f"Tree 'MuonAndSoftInteractions' not found in file")
    file.Close()
    exit(1)

print(f"Processing tree: {tree.GetName()}")
print(f"Total number of entries: {tree.GetEntries()}")

for event in tree:

    imuondata = event.imuondata  
    pid = imuondata[0]
    px = imuondata[1]
    py = imuondata[2]
    pz = imuondata[3]
    x = imuondata[4]
    y = imuondata[5]
    z = imuondata[6]
    weight = imuondata[7]
    time_hit = imuondata[8]

    num_tracks = len(event.tracks) 
    
    print(f"Muon PID: {pid},  x: {x}, y: {y}, z: {z}, t_muon: {time_hit}, Number of soft tracks in this event: {num_tracks}")
    

file.Close()

#python make_nTuple_Tr.py -p <path to muonbackground files>


