// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration


#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;

#pragma link C++ class ShipStack+;
#pragma link C++ class ShipMCTrack+;
#pragma link C++ class ShipParticle+;
// Up to version 3, particles had exactly two daughters
#pragma read sourceClass="ShipParticle" targetClass="ShipParticle" version="[-3]" source="Int_t fDaughter[2]" target="fDaughters" code="{ fDaughters.assign(onfile.fDaughter, onfile.fDaughter + 2); }"
#pragma link C++ class TrackInfo+;
#pragma link C++ class EventHistogram-;
#pragma link C++ namespace SHiP;
#pragma link C++ class SHiP::RecoTrack+;
#pragma link C++ class SHiP::RecoVertex+;
// Vertices of version 1 came from fits without track weights
#pragma read sourceClass="SHiP::RecoVertex" targetClass="SHiP::RecoVertex" version="[1]" source="std::vector<Int_t> m_trackIds" target="m_trackWeights" code="{ m_trackWeights.assign(onfile.m_trackIds.size(), 1.); }"
#pragma link C++ class std::vector<SHiP::RecoTrack>+;
#pragma link C++ class std::vector<SHiP::RecoVertex>+;
#pragma link C++ class ISTLPointContainer-;
#pragma link C++ class std::vector<ShipParticle>+;
#pragma link C++ class std::vector<genfit::Track*>+;
#pragma link C++ class std::vector<std::vector<int>>+;
#pragma link C++ class std::vector<std::vector<float>>+;

#endif
