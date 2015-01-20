from ROOT import *
Na = 6.022e23 # numero avogadro: mol-1

## massa molare
A1 = 55.847 #Fe: [g/mol]
rho1 = 7874*1e+3/(1e+6)#Fe: 7874[kg/m3]
E10 = 10 #GeV
sigma10 = 0.68*E10*1.e-38 #E in GeV
LambdaFe10 = A1/(Na * rho1 * sigma10)
print '# (E=10GeV)', 1./LambdaFe10*5*1e-2*5e+16

E50 = 50 #GeV
sigma50 = 0.68*E50*1.e-38 #E in GeV
LambdaFe50 = A1/(Na * rho1 * sigma50)
print '# (E=50GeV)', 1./LambdaFe50*5*1e-2*5e+16

## massa molare
A2 = 26.98 #Al: [g/mol]
rho2 = 2700*1e+3/(1e+6)#Al: 7874[kg/m3]
LambdaAl10 = A2/(Na * rho2 * sigma10)
LambdaAl50 = A2/(Na * rho2 * sigma50)
#print Lambda


## windows first Fe (3cm) second Al (0.8cm)
L1  = 3.e-2
L2 = 0.8e-2

frac_n1n2 = (L1*rho1/A1) / (L2*rho2/A2)
print "n1/n2 = %s"%frac_n1n2

print "# expect 1window for 10^16 nu (10GeV)", 1./LambdaFe10 * 3e-2*5e+16
print "# expect 2window for 10^16 nu (10GeV)", 1./LambdaAl10 * 0.8e-2*5e+16
print "# expect 1window for 10^16 nu (50GeV)", 1./LambdaFe50 * 3e-2*5e+16
print "# expect 2window for 10^16 nu (50GeV)", 1./LambdaAl50 * 0.8e-2*5e+16

