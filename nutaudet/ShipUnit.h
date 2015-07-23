//
//  ShipUnit.h
//
//

#ifndef ____ShipUnit__
#define ____ShipUnit__

namespace ShipUnit
{
    
    //
    // Length [L]
    //
    static const Double_t millimeter  = 1./10.;
    static const Double_t millimeter2 = millimeter*millimeter;
    static const Double_t millimeter3 = millimeter*millimeter*millimeter;
    
    static const Double_t centimeter  = 10.*millimeter;
    static const Double_t centimeter2 = centimeter*centimeter;
    static const Double_t centimeter3 = centimeter*centimeter*centimeter;
    
    static const Double_t meter  = 1000.*millimeter;
    static const Double_t meter2 = meter*meter;
    static const Double_t meter3 = meter*meter*meter;
    
    static const Double_t kilometer = 1000.*meter;
    static const Double_t kilometer2 = kilometer*kilometer;
    static const Double_t kilometer3 = kilometer*kilometer*kilometer;
    
    static const Double_t parsec = 3.0856775807e+16*meter;
    
    static const Double_t micrometer = 1.e-6 *meter;
    static const Double_t  nanometer = 1.e-9 *meter;
    static const Double_t  angstrom  = 1.e-10*meter;
    static const Double_t  fermi     = 1.e-15*meter;
    
    static const Double_t      barn = 1.e-28*meter2;
    static const Double_t millibarn = 1.e-3 *barn;
    static const Double_t microbarn = 1.e-6 *barn;
    static const Double_t  nanobarn = 1.e-9 *barn;
    static const Double_t  picobarn = 1.e-12*barn;
    
    // symbols
    static const Double_t nm  = nanometer;
    static const Double_t um  = micrometer;
    
    static const Double_t mm  = millimeter;
    static const Double_t mm2 = millimeter2;
    static const Double_t mm3 = millimeter3;
    
    static const Double_t cm  = centimeter;
    static const Double_t cm2 = centimeter2;
    static const Double_t cm3 = centimeter3;
    
    static const Double_t m  = meter;
    static const Double_t m2 = meter2;
    static const Double_t m3 = meter3;
    
    static const Double_t km  = kilometer;
    static const Double_t km2 = kilometer2;
    static const Double_t km3 = kilometer3;
    
    static const Double_t pc = parsec;
    
    //
    // Angle
    //
    static const Double_t radian      = 1.;
    static const Double_t milliradian = 1.e-3*radian;
    static const Double_t degree = (3.14159265358979323846/180.0)*radian;
    
    static const Double_t   steradian = 1.;
    
    // symbols
    static const Double_t rad  = radian;
    static const Double_t mrad = milliradian;
    static const Double_t sr   = steradian;
    static const Double_t deg  = degree;
    
    //
    // Time [T]
    //
    static const Double_t nanosecond  = 1.;
    static const Double_t second      = 1.e+9 *nanosecond;
    static const Double_t millisecond = 1.e-3 *second;
    static const Double_t microsecond = 1.e-6 *second;
    static const Double_t  picosecond = 1.e-12*second;
    
    static const Double_t hertz = 1./second;
    static const Double_t kilohertz = 1.e+3*hertz;
    static const Double_t megahertz = 1.e+6*hertz;
    
    // symbols
    static const Double_t ns = nanosecond;
    static const Double_t  s = second;
    static const Double_t ms = millisecond;
    
    //
    // Electric charge [Q]
    //
    static const Double_t eplus = 1. ;// positron charge
    static const Double_t e_SI  = 1.602176487e-19;// positron charge in coulomb
    static const Double_t coulomb = eplus/e_SI;// coulomb = 6.24150 e+18 * eplus
    
    //
    // Energy [E]
    //
    static const Double_t megaelectronvolt = 1. ;
    static const Double_t     electronvolt = 1.e-6*megaelectronvolt;
    static const Double_t kiloelectronvolt = 1.e-3*megaelectronvolt;
    static const Double_t gigaelectronvolt = 1.e+3*megaelectronvolt;
    static const Double_t teraelectronvolt = 1.e+6*megaelectronvolt;
    static const Double_t petaelectronvolt = 1.e+9*megaelectronvolt;
    
    static const Double_t joule = electronvolt/e_SI;// joule = 6.24150 e+12 * MeV
    
    // symbols
    static const Double_t MeV = megaelectronvolt;
    static const Double_t  eV = electronvolt;
    static const Double_t keV = kiloelectronvolt;
    static const Double_t GeV = gigaelectronvolt;
    static const Double_t TeV = teraelectronvolt;
    static const Double_t PeV = petaelectronvolt;
    
    //
    // Mass [E][T^2][L^-2]
    //
    static const Double_t  kilogram = joule*second*second/(meter*meter);
    static const Double_t      gram = 1.e-3*kilogram;
    static const Double_t milligram = 1.e-3*gram;
    
    // symbols
    static const Double_t  kg = kilogram;
    static const Double_t   g = gram;
    static const Double_t  mg = milligram;
    
    //
    // Power [E][T^-1]
    //
    static const Double_t watt = joule/second;// watt = 6.24150 e+3 * MeV/ns
    
    //
    // Force [E][L^-1]
    //
    static const Double_t newton = joule/meter;// newton = 6.24150 e+9 * MeV/mm
    
    //
    // Pressure [E][L^-3]
    //
    #define pascal hep_pascal                          // a trick to avoid warnings
    static const Double_t hep_pascal = newton/m2;   // pascal = 6.24150 e+3 * MeV/mm3
    static const Double_t bar        = 100000*pascal; // bar    = 6.24150 e+8 * MeV/mm3
    static const Double_t atmosphere = 101325*pascal; // atm    = 6.32420 e+8 * MeV/mm3
    
    //
    // Electric current [Q][T^-1]
    //
    static const Double_t      ampere = coulomb/second; // ampere = 6.24150 e+9 * eplus/ns
    static const Double_t milliampere = 1.e-3*ampere;
    static const Double_t microampere = 1.e-6*ampere;
    static const Double_t  nanoampere = 1.e-9*ampere;
    
    //
    // Electric potential [E][Q^-1]
    //
    static const Double_t megavolt = megaelectronvolt/eplus;
    static const Double_t kilovolt = 1.e-3*megavolt;
    static const Double_t     volt = 1.e-6*megavolt;
    
    //
    // Electric resistance [E][T][Q^-2]
    //
    static const Double_t ohm = volt/ampere;// ohm = 1.60217e-16*(MeV/eplus)/(eplus/ns)
    
    //
    // Electric capacitance [Q^2][E^-1]
    //
    static const Double_t farad = coulomb/volt;// farad = 6.24150e+24 * eplus/Megavolt
    static const Double_t millifarad = 1.e-3*farad;
    static const Double_t microfarad = 1.e-6*farad;
    static const Double_t  nanofarad = 1.e-9*farad;
    static const Double_t  picofarad = 1.e-12*farad;
    
    //
    // Magnetic Flux [T][E][Q^-1]
    //
    static const Double_t weber = volt*second;// weber = 1000*megavolt*ns
    
    //
    // Magnetic Field [T][E][Q^-1][L^-2]
    //
    //static const Double_t tesla     = volt*second/meter2;// tesla =0.001*megavolt*ns/mm2
    //static const Double_t gauss     = 1.e-4*tesla;
    //static const Double_t kilogauss = 1.e-1*tesla;

	static const Double_t kilogauss = 1.;
	static const Double_t tesla     = 10*kilogauss;
	static const Double_t gauss     = 1.e-4*tesla;
    
    //
    // Inductance [T^2][E][Q^-2]
    //
    static const Double_t henry = weber/ampere;// henry = 1.60217e-7*MeV*(ns/eplus)**2
    
    //
    // Temperature
    //
    static const Double_t kelvin = 1.;
    
    //
    // Amount of substance
    //
    static const Double_t mole = 1.;
    
    //
    // Activity [T^-1]
    //
    static const Double_t becquerel = 1./second ;
    static const Double_t curie = 3.7e+10 * becquerel;
    static const Double_t kilobecquerel = 1.e+3*becquerel;
    static const Double_t megabecquerel = 1.e+6*becquerel;
    static const Double_t gigabecquerel = 1.e+9*becquerel;
    static const Double_t millicurie = 1.e-3*curie;
    static const Double_t microcurie = 1.e-6*curie;
    static const Double_t Bq = becquerel;
    static const Double_t kBq = kilobecquerel;
    static const Double_t MBq = megabecquerel;
    static const Double_t GBq = gigabecquerel;
    static const Double_t Ci = curie;
    static const Double_t mCi = millicurie;
    static const Double_t uCi = microcurie;
    
    //
    // Absorbed dose [L^2][T^-2]
    //
    static const Double_t      gray = joule/kilogram ;
    static const Double_t  kilogray = 1.e+3*gray;
    static const Double_t milligray = 1.e-3*gray;
    static const Double_t microgray = 1.e-6*gray;
    
    //
    // Luminous intensity [I]
    //
    static const Double_t candela = 1.;
    
    //
    // Luminous flux [I]
    //
    static const Double_t lumen = candela*steradian;
    
    //
    // Illuminance [I][L^-2]
    //
    static const Double_t lux = lumen/meter2;
    
    //
    // Miscellaneous
    //
    static const Double_t perCent     = 0.01 ;
    static const Double_t perThousand = 0.001;
    static const Double_t perMillion  = 0.000001;
    
    //
    //Physical Constants
    //
    
    static const Double_t pi     = 3.14159265358979323846;
    static const Double_t twopi  = 2.*pi;
    static const Double_t halfpi = pi/2.;
    static const Double_t pi2    = pi*pi;
    
    //
    static const Double_t Avogadro = 6.0221367e+23/mole;
    
    // c   = 299.792458 mm/ns
    // c^2 = 898.7404 (mm/ns)^2
    static const Double_t c_light   = 2.99792458e+8 * m/s;
    static const Double_t  c_squared = c_light * c_light;
    
    // h     = 4.13566e-12 MeV*ns
    // hbar  = 6.58212e-13 MeV*ns
    // hbarc = 197.32705e-12 MeV*mm
    static const Double_t h_Planck      = 6.6260755e-34 * joule*s;
    static const Double_t hbar_Planck   = h_Planck/twopi;
    static const Double_t hbarc         = hbar_Planck * c_light;
    static const Double_t hbarc_squared = hbarc * hbarc;
    
    //
    static const Double_t electron_charge = - eplus; // see SystemOfUnits.h
    static const Double_t e_squared = eplus * eplus;
    
    // amu_c2 - atomic equivalent mass unit
    // amu    - atomic mass unit
    static const Double_t electron_mass_c2 = 0.51099906 * MeV;
    static const Double_t proton_mass_c2 = 938.27231 * MeV;
    static const Double_t neutron_mass_c2 = 939.56563 * MeV;
    static const Double_t amu_c2 = 931.49432 * MeV;
    static const Double_t amu = amu_c2/c_squared;
    
    // permeability of free space mu0    = 2.01334e-16 Mev*(ns*eplus)^2/mm
    // permittivity of free space epsil0 = 5.52636e+10 eplus^2/(MeV*mm)
    static const Double_t mu0      = 4*pi*1.e-7 * henry/m;
    static const Double_t epsilon0 = 1./(c_squared*mu0);
    
    // electromagnetic coupling = 1.43996e-12 MeV*mm/(eplus^2)
    static const Double_t elm_coupling           = e_squared/(4*pi*epsilon0);
    static const Double_t fine_structure_const   = elm_coupling/hbarc;
    static const Double_t classic_electr_radius  = elm_coupling/electron_mass_c2;
    static const Double_t electron_Compton_length = hbarc/electron_mass_c2;
    static const Double_t Bohr_radius = electron_Compton_length/fine_structure_const;
    
    static const Double_t alpha_rcl2 = fine_structure_const * classic_electr_radius * classic_electr_radius;
    static const Double_t  twopi_mc2_rcl2 = twopi * electron_mass_c2 * classic_electr_radius * classic_electr_radius;
    
    //
    static const Double_t k_Boltzmann = 8.617385e-11 * MeV/kelvin;
    
    //
    static const Double_t STP_Temperature = 273.15*kelvin;
    static const Double_t STP_Pressure    = 1.*atmosphere;
    static const Double_t kGasThreshold   = 10.*mg/cm3;
    
    //
    static const Double_t universe_mean_density = 1.e-25*g/cm3;
    
    
    };
    
#endif /* defined(____ShipUnit__) */
