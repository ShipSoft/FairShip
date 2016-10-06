void DecayConfig() {
     
	// This script uses the external decayer TPythia8Decayer in place of the
	// concrete Monte Carlo native decay mechanisms only for the
	// specific types of decays defined below.
	
	// Access the external decayer singleton and initialize it  
	TPythia8Decayer* decayer = new TPythia8Decayer();
	decayer->SetDebugLevel(1);
        TPythia8* tp8 = TPythia8::Instance();
        tp8->ReadString("ProcessLevel:all = off");
        // example how to overwrite decay table
        // tp8->ReadString("15:new  tau-             tau+               2  -3   0    1.77682    0.00000    0.00000    0.00000  8.71100e-02   0   0   0   1   0");
        // tp8->ReadString("15:addChannel      1   1    0    16   13  ");       
	decayer->Init();
	// Tell the concrete monte carlo to use the external decayer.  The
	// external decayer will be used for:
	// i)particle decays not defined in concrete monte carlo, or
	//ii)particles for which the concrete monte carlo is told
	//   to use the external decayer for its type via:
	//     gMC->SetUserDecay(pdgId);
	//   If this is invoked, the external decayer will be used for particles 
	//   of type pdgId even if the concrete monte carlo has a decay mode 
	//   already defined for that particle type.
	gMC->SetExternalDecayer(decayer);
        gMC->SetUserDecay(411);
        gMC->SetUserDecay(-411);
        tp8->ReadString("411:mayDecay = off");
        gMC->SetUserDecay(421);
        gMC->SetUserDecay(-421);
        tp8->ReadString("421:mayDecay = off");
        gMC->SetUserDecay(4122);
        gMC->SetUserDecay(-4122);
        tp8->ReadString("15:mayDecay = off"); 
        gMC->SetUserDecay(431);
        gMC->SetUserDecay(-431);
        tp8->ReadString("431:mayDecay = off"); 
        gMC->SetUserDecay(15);
        gMC->SetUserDecay(-15);
        tp8->ReadString("15:mayDecay = off");
}
