void DecayConfig() {
     
	// This script uses the external decayer TPythia8Decayer in place of the
	// concrete Monte Carlo native decay mechanisms only for the
	// specific types of decays defined below.
	
	// Access the external decayer singleton and initialize it  
	TVirtualMCDecayer* decayer = new TPythia8Decayer();
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
        // to get the rare muon decays, HOWEVER does not work with Geant4 logic
        //gMC->SetUserDecay(221); // eta
        //gMC->SetUserDecay(223); // omega
        //gMC->SetUserDecay(113); // rho0
        //gMC->SetUserDecay(331); // eta_prime
        //gMC->SetUserDecay(333); // phi
        gMC->SetUserDecay(411);
        gMC->SetUserDecay(-411);
        gMC->SetUserDecay(421);
        gMC->SetUserDecay(-421);
        gMC->SetUserDecay(4122);
        gMC->SetUserDecay(-4122);
        gMC->SetUserDecay(431);
        gMC->SetUserDecay(-431);
        gMC->SetUserDecay(15);
        gMC->SetUserDecay(-15);
        cout<< "External decayer DecayConfigPy8 initialized"<<endl;
}


