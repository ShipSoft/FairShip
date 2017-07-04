import G4particles,G4global,ROOT
def Initialize(p8):
# take decay and brancing ratios from Pythia8
  pt = G4particles.G4ParticleTable.GetParticleTable()
  for vreso in [223,333,113]:
   particleG4  = pt.FindParticle(vreso)
   particleP8  = p8.particleData.particleDataEntryPtr(vreso)
   decayTable =  G4particles.G4DecayTable()
   for i in range(particleP8.sizeChannels()):
    achannel = particleP8.channel(i)
    bR  = achannel.bRatio()
    mul = achannel.multiplicity()
    dl = []
    for daughter in range(4):
      if daughter<mul:
       pid = achannel.product(daughter) 
       dl.append(pt.FindParticle(pid).GetParticleName())
      else:  dl.append("")
    mode  = G4particles.G4PhaseSpaceDecayChannel(particleG4.GetParticleName(),bR,mul,dl[0],dl[1],dl[2],dl[3])
    decayTable.Insert(mode)
   particleG4.SetDecayTable(decayTable)
   particleG4.DumpTable()
