#!/usr/bin/python

import ROOT#
import numpy as np
import math
from math import exp, sqrt, log, ceil
import random
import matplotlib.pyplot as plt

from ROOT.TMath import Landau, Gaus, Poisson
from ShipGeoConfig import ConfigRegistry

#####################################################
##########  GLOBAL VALUES AND PARAMETERS ############
#####################################################

# Position of SiPMs in the detector (left/right and up/down)
sipm_hor_pos = +1 # at X = +len_vert / 2 
sipm_vert_pos = -1 # at Y = -len_hor /  2

# If reversed is true the channels counted in reverse way
# (0->1535 => 1535<-0). It connected with how the modules are placed
is_sipm_hor_reversed = True
is_sipm_vert_reversed = True

# SiPM geometry
# hw - half width
# pitch - one channel width
# charr - array of 64 channels without gaps 
# edge - from left and right sides of the SiPM
# gap - between two charr 
# array - 128 channels with the gap
# biggap - gap between two arrays 
# ch_max_num - max channel in the SiPM (0-1535) 
# n_solid_sipms - number of "charr" arrays
# Total SiPM size is 32.54 mm

hw = 19.528 				# Position of the first SiPM   
pitch = 0.025
charr = 1.6
edge = 0.016 
gap = 0.022 				# Die gap
array = gap + 2.*charr
biggap = 0.038 				# 0.006cm is the space between SiPMs, plus 2*edge (in CAD SiPMs are separated by 32.60 mm)
ch_max_num = 128*12 - 1		# numbering from 0 to 1535
n_solid_sipms = 12 

# SiPM geometry. If a point is in the solid part then the position will be counted.
# Else false value returns. 
sipm_map = (
	(-hw, -hw+edge, False),
	(-hw+edge, -hw+edge+charr, (-0.5, 63.5)),														# 1.1
	(-hw+edge+charr, -hw+edge+charr+gap, False),
	(-hw+edge+charr+gap, -hw+edge+array, (63.5, 127.5)),											# 1.2
	(-hw+edge+array, -hw+edge+array+biggap, False),
	(-hw+edge+array+biggap, -hw+edge+array+biggap+charr, (127.5, 191.5)),							# 2.1
	(-hw+edge+array+biggap+charr, -hw+edge+array+biggap+charr+gap, False),
	(-hw+edge+array+biggap+charr+gap, -hw+edge+array+biggap+array, (191.5, 255.5)),					# 2.2
	(-hw+edge+2*array+biggap, -hw+edge+2*array+2*biggap, False),
	(-hw+edge+2*array+2*biggap, -hw+edge+2*array+2*biggap+charr, (255.5, 319.5)),					# 3.1
	(-hw+edge+2*array+2*biggap+charr, -hw+edge+2*array+2*biggap+charr+gap, False),
	(-hw+edge+2*array+2*biggap+charr+gap, -hw+edge+2*array+2*biggap+array, (319.5, 383.5)),			# 3.2	
	(-hw+edge+3*array+2*biggap, -hw+edge+3*array+3*biggap, False),
	(-hw+edge+3*array+3*biggap, -hw+edge+3*array+3*biggap+charr, (383.5, 447.5)),			    	# 4.1
	(-hw+edge+3*array+3*biggap+charr, -hw+edge+3*array+3*biggap+charr+gap, False),
	(-hw+edge+3*array+3*biggap+charr+gap, -hw+edge+3*array+3*biggap+array, (447.5, 511.5)),			# 4.2	

	(-hw+edge+4*array+3*biggap, -hw+edge+4*array+4*biggap, False),
	(-hw+edge+4*array+4*biggap, -hw+edge+4*array+4*biggap+charr, (511.5, 575.5)),					# 5.1
	(-hw+edge+4*array+4*biggap+charr, -hw+edge+4*array+4*biggap+charr+gap, False),
	(-hw+edge+4*array+4*biggap+charr+gap, -hw+edge+4*array+4*biggap+array, (575.5, 639.5)),			# 5.2	
	(-hw+edge+5*array+4*biggap, -hw+edge+5*array+5*biggap, False),
	(-hw+edge+5*array+5*biggap, -hw+edge+5*array+5*biggap+charr, (639.5, 703.5)),					# 6.1
	(-hw+edge+5*array+5*biggap+charr, -hw+edge+5*array+5*biggap+charr+gap, False),
	(-hw+edge+5*array+5*biggap+charr+gap, -hw+edge+5*array+5*biggap+array, (703.5, 767.5)),			# 6.2	
	(-hw+edge+6*array+5*biggap, -hw+edge+6*array+6*biggap, False),
	(-hw+edge+6*array+6*biggap, -hw+edge+6*array+6*biggap+charr, (767.5, 831.5)),					# 7.1
	(-hw+edge+6*array+6*biggap+charr, -hw+edge+6*array+6*biggap+charr+gap, False),
	(-hw+edge+6*array+6*biggap+charr+gap, -hw+edge+6*array+6*biggap+array, (831.5, 895.5)),			# 7.2	
	(-hw+edge+7*array+6*biggap, -hw+edge+7*array+7*biggap, False),
	(-hw+edge+7*array+7*biggap, -hw+edge+7*array+7*biggap+charr, (895.5, 959.5)),					# 8.1
	(-hw+edge+7*array+7*biggap+charr, -hw+edge+7*array+7*biggap+charr+gap, False),
	(-hw+edge+7*array+7*biggap+charr+gap, -hw+edge+7*array+7*biggap+array, (959.5, 1023.5)),		# 8.2	

	(-hw+edge+8*array+7*biggap, -hw+edge+8*array+8*biggap, False),
	(-hw+edge+8*array+8*biggap, -hw+edge+8*array+8*biggap+charr, (1023.5, 1087.5)),					# 9.1
	(-hw+edge+8*array+8*biggap+charr, -hw+edge+8*array+8*biggap+charr+gap, False),
	(-hw+edge+8*array+8*biggap+charr+gap, -hw+edge+8*array+8*biggap+array, (1087.5, 1151.5)),		# 9.2	
	(-hw+edge+9*array+8*biggap, -hw+edge+9*array+9*biggap, False),
	(-hw+edge+9*array+9*biggap, -hw+edge+9*array+9*biggap+charr, (1151.5, 1215.5)),					# 10.1
	(-hw+edge+9*array+9*biggap+charr, -hw+edge+9*array+9*biggap+charr+gap, False),
	(-hw+edge+9*array+9*biggap+charr+gap, -hw+edge+9*array+9*biggap+array, (1215.5, 1279.5)),		# 10.2	
	(-hw+edge+10*array+9*biggap, -hw+edge+10*array+10*biggap, False),
	(-hw+edge+10*array+10*biggap, -hw+edge+10*array+10*biggap+charr, (1279.5, 1343.5)),				# 11.1
	(-hw+edge+10*array+10*biggap+charr, -hw+edge+10*array+10*biggap+charr+gap, False),
	(-hw+edge+10*array+10*biggap+charr+gap, -hw+edge+10*array+10*biggap+array, (1343.5, 1407.5)),	# 11.2	
	(-hw+edge+11*array+10*biggap, -hw+edge+11*array+11*biggap, False),
	(-hw+edge+11*array+11*biggap, -hw+edge+11*array+11*biggap+charr, (1407.5, 1471.5)),		#12.1
	(-hw+edge+11*array+11*biggap+charr, -hw+edge+11*array+11*biggap+charr+gap, False),
	(-hw+edge+11*array+11*biggap+charr+gap, -hw+edge+11*array+11*biggap+array, (1471.5, 1535.5))	#12.2	

)

# If a point is in the dead space then the following channel value will be selected
gaps_map = {
	0.: -0.5, 
	1.: 63.5,
	2.: 127.5, 
	3.: 191.5,
	4.: 255.5, 
	5.: 319.5,
	6.: 383.5,
	7.: 447.5,
 
	8.: 511.5,
	9.: 575.5, 
	10.: 639.5,
	11.: 703.5, 
	12.: 767.5,
	13.: 831.5, 
	14.: 895.5,
	15.: 959.5,

	16.: 1023.5, 
	17.: 1087.5,
	18.: 1151.5, 
	19.: 1215.5,
	20.: 1279.5, 
	21.: 1343.5,
	22.: 1407.5, 
	23.: 1471.5,
	24.: 1535.5
}

# 1st mat gap is from -62.28mm -> -61.78mm ; 521.5 -> 523.5 channel
# 2nd mat gap is from 71.22mm -> 71.72 mm ; 1046.5 -> 1048.5  channel
# the gaps start and end inside these channels
firstmatgap_startch = 521.5
firstmatgap_endch = 523.5 
secmatgap_startch = 1046.5
secmatgap_endch = 1048.5

# Possible values of channel position and cluster width
chpos_min = -0.5
chpos_max = 1535.5
cluster_width_min = 1
cluster_width_max = 10

#------------------ former values from SHiP's Target Tracker-------------------------------- 

# Light yield attenuation A*exp(B*x) + C*exp(D*x)
# Sigma depends on the distance from a SiPM and also the following parameters 
ly_loss_params = 20.78, -0.26, 7.89, -3.06
ly_loss_sigma_params = 	6.8482, -0.5757, 3.4458
cluster_width_mean_params = 0.6661, -0.006955, 2.163
cluster_width_sigma_params = 1.103, -0.0005751

# The random width in the range is manually set as 1% of events
# It covers cases where the width is 5-10 
random_width_percent = 0.01 

# Possible values of LY
ly_min = 4.5
ly_max = 104

# Energy deposit converts in the light yield range linearly. Energy less then 0.18 MeV gives doesn't registered.
# Energy more then 0.477 MeV converts randomly with approximation distribution.
energy_range = 0.18, 0.477

# The maximum value of the CDF integral 
CDF_integral = 0.0185640424

# Parameters that are used for linear conversion of deposit energy to the range 
# equal to the light yield range
ly_linear_params = 332.882, -58.7085

# The coefficient between the maximums of CDF(E) and CDF(LY), a little differs
k_cdfs_corr = 0.993076766938

# The addition of a little randomness in the converting from the energy distibution to 
# the light yield distibution
sigma_in_percent = 0.01

# 4 sigma range includes 95% of events. It needs for creating a cluster
sigma_from_width = 1 / 4.

# The following parameters will be used in the converting from the energy distibution to the light yield distibution.
# Dictionaries format is following - (x_min, x_max) : (parameters), approximating function.

# ly_CDF_params - approximation of CDF of the light yield distribution. 
# If is doesn't used already.
ly_CDF_params = {
	(4.5, 13): (
		(-13.2, 1.976), 
		lambda ly, *p: exp(p[0] + p[1]*sqrt(ly))
	),
	(13, 104): (
		(0.0108183, -0.179752, -19.2, 0.00772965),
		lambda ly, *p: p[0]*(1 - exp(p[1]*(ly+p[2]))) / (1 + exp(p[1]*(ly+p[2]))) + p[3]
	)
}


# Get a CDF value from LY (actually from an energy deposit which preliminarily linearly 
# converted to the range of the light yield (4.5 - 104 ph.e.)
ly_CDF_landau_params = {
	(4.5, 15): (
		(0.001038, -0.000378, 3.53e-05), 
		lambda ly, *p: p[0] + p[1]*ly + p[2]*ly**2
	),
	(15, 40): (
		(-0.001986, -0.0003014, 7.031e-05, -2.067e-06, 1.892e-08),
		lambda ly, *p: p[0] + p[1]*ly + p[2]*ly**2 + p[3]*ly**3 + p[4]*ly**4
	),
	(40, 104): (
		(-0.007149, 0.001056, -1.779e-05, 1.41e-07, -4.29e-10),
		lambda ly, *p: p[0] + p[1]*ly + p[2]*ly**2 + p[3]*ly**3 + p[4]*ly**4
	)
}

# Get a light yield value from a CDF values
CDF_ly_params = {
	(0., 0.0006): (
		(89., 4.152, 0.0001574, -1.326e+04, 4.3), 
		lambda cdf, *p: p[0] * sqrt(p[1]*(cdf+p[2])) * (1-exp(p[3]*cdf)) + p[4]
	),
	(0.0006, 0.012): (
		(158, 1.035, 0.24, 217),
		lambda cdf, *p: p[0] * log(sqrt(cdf)+p[1]) + p[2]*exp(p[3]*cdf)
	),
	(0.012, 0.018561405): (
		(9.36, 335.984, -18100, -400, 15),
		lambda cdf, *p: p[0] * log((p[1]-p[2]*cdf)/(p[1]+p[2]*cdf)) + p[3]*cdf + p[4]
	),
	(0.018561405, 0.0185640424): (
		(9.36, 335.984, -18100, -400, 15),
		lambda cdf, *p: (p[0] * log((p[1]-p[2]*0.018561405)/(p[1]+p[2]*0.018561405)) 
			+ p[3]*0.018561405 + p[4])
	)
}

#------------------------------------------------------------------------------------

##################################################
###########  LOAD THE SCIFI GEOMETRY  ############
##################################################

snd_geo = ConfigRegistry.loadpy("$SNDSW_ROOT/geometry/shipLHC_geom_config.py") 

scifimat_width = snd_geo.Scifi.scifimat_width    # 13.3 cm
scifimat_length = snd_geo.Scifi.scifimat_length  # 40 cm
scifimat_gap = snd_geo.Scifi.scifimat_gap        # 0.05 cm

scifi_x = snd_geo.Scifi.xdim 		 			 # 40 cm
scifi_y = snd_geo.Scifi.ydim 		 			 # 40 cm
scifimat_z = snd_geo.Scifi.scifimat_z            # 0.135 cm

nmats = snd_geo.Scifi.nmats                      # 3
n_planes = snd_geo.Scifi.nscifi                  # 5
n_sipms = snd_geo.Scifi.nsipms                   # 12 per plane

#############################################################################
#############################################################################
####### Need to automatize this part so it works for every geometry #########
#############################################################################
#############################################################################

#from getGeoInformation.py
xshift = -27.8
yshift = +35.3

#########################################################################################
#####    FUNCTIONS FOR SCIFICLASS      ##################################################
#########################################################################################

def cm_to_channel(locpos, sipm_map=sipm_map, gaps_map=gaps_map, pitch=pitch, charr=charr,
				  reverse=False, ch_max_num=ch_max_num, n_solid_sipms=n_solid_sipms):
	
	"""
	It converts a particle position (an event) measured in cm to a position measured 
	in channels. The SiPM map is used. The position is in the scifi module frame.
	"""
	
	if reverse is True:
		for left, right, ch_range in sipm_map:
			if left <= locpos <= right:
				if not ch_range is False:
					ch_start = ch_range[0]
					return int(round(ch_max_num - ((locpos-left) / pitch + ch_start)))
				else:
					mapindex = int(round(n_solid_sipms - (locpos + hw) / charr))
					return gaps_map.get(mapindex, False)

	elif reverse is False:
		for left, right, ch_range in sipm_map:
			if left <= locpos <= right:
				if not ch_range is False:
					ch_start = ch_range[0]
					return int(round(locpos-left) / pitch + ch_start)
				else:
					mapindex2 = int(round(locpos + hw) / charr)
					return gaps_map.get( mapindex2, False)
 
def channel_to_cm(channelpos, sipm_map=sipm_map, reverse=False, pitch=pitch):

	"""
	It converts a particle position measured channels to a position measured 
	in cm. The SiPM map is used. The position is in the scifi module frame.
	"""

	if reverse is True:
		for left, _, ch_range in sipm_map:
			if not ch_range is False:
				ch_start, ch_end = ch_range
				if ch_start <= channelpos <= ch_end:
					return -(left + (channelpos - ch_start) * pitch)
	if reverse is False:
		for left, _, ch_range in sipm_map:
			if not ch_range is False:
				ch_start, ch_end = ch_range
				if ch_start <= channelpos <= ch_end:
					return left + (channelpos - ch_start) * pitch

def GetMatType(DetID):
    
	"""
	It returns a type of a scifi module.
	1 - vertical scifi assembly
	0 - horizontal scifi assembly
	"""
	return int((DetID % 100) // 10)


def GetMatNum(DetID):

	"""
	It returns an id (number) of a scifi module. In current version one plane has 3 vertical
	and 3 horizontal scifi assemblies. 
	"""

	return int(DetID % 100 % 10)

def GetMatLength():

	"""
	It returns a length of a scifi mat. Identical for vertical and horizontal.
	"""
 
	return scifimat_length

def GetMatQty():

	"""
	It returns a number of scifi mats in a plane. Identical for vertical and horizontal fiber planes.
	"""
 	
	return n_planes

def GetSiPMs():
    
    """
	It returns a number of SiPMs per plane. Identical for vertical and horizontal fiber planes.
	"""
    
    return n_sipms

def GetStationNum(DetID):

	"""
	It returns an id of a plane. In current version the detector has 5 TT stations (numbering starts
	at 1.
	"""
	return int(DetID // 100)

##############################################################################
##### These functions assume that the detector is aligned with the beam ######
##############################################################################

def global_to_local(DetID, globalpos):

	"""
	It returns the local coordinates in one scifi assembly frame from global coordinates.
	"""
	
	global xshift, yshift

	if GetMatType(DetID) == 0:
		return globalpos - yshift
	
	if GetMatType(DetID) == 1:
		return globalpos - xshift


def local_to_global(DetID, localpos):

	"""
	It returns the global coordinates from the local coordinates in one scifi assembly frame.
	"""

	global xshift, yshift

	if GetMatType(DetID) == 0:
		return localpos + yshift

	if GetMatType(DetID) == 1:
		return localpos + xshift

############################################################################

def ly_loss_mean(distance, params=ly_loss_params):

	"""
	It returns the light yield depending on the distance to SiPMs
	"""

	A1, k1, A2, k2 = params
	return A1 * exp(k1 * distance / 100.) + A2 * exp(k2 * distance / 100.)

def ly_attenuation(distance):

	"""
	It return the light yield losses in percent depending on the distance to SiPMs
	"""

	res_ly_loss = ly_loss_mean(distance) / ly_loss_mean(0.) 
	return res_ly_loss

def cluster_width_mean(distance, params=cluster_width_mean_params):

	"""
	It return a mean cluster width depending on the distance to SiPMs
	"""

	A, B, C = params
	return exp(A + B*distance) + C

def cluster_width_sigma(distance, params=cluster_width_sigma_params):

	"""
	It return a standard deviation of the mean cluster width depending on the distance to SiPMs
	"""

	A, B = params
	return A + B*distance

def cluster_width_random(distance, ly, percent=random_width_percent, 
						 cluster_width_min=cluster_width_min, cluster_width_max=cluster_width_max):
	
	"""
	It generates a cluster. The cluster have 'ly' photoelectrons. 
	The cluster width depends on the distance to SiPM
	"""

	mean = cluster_width_mean(distance)
	sigma = cluster_width_sigma(distance)
	if random.random() <= percent:
		return random.randint(cluster_width_min, cluster_width_max)
	random_width = int(round(random.gauss(mean - 1, sigma))) + 1

	# Generate again if the width < minimal width and the light yield < the width
	while random_width < 1 or ly < random_width:
		random_width = int(round(random.gauss(mean - 1, sigma))) + 1

	return random_width

def approx_function(var, approx_data):

	"""
	This universal function substitutes the parameters to the function. 
	The parameters and the function are in the dictionary
	"""

	for (left, right), (params, func) in approx_data.items():
		if left <= var <= right:
			return func(var, *params)
	return False

def edep_to_ly(energy, CDF_integral=CDF_integral, energy_range=energy_range, 
	ly_linear_params=ly_linear_params, k_cdfs_corr=k_cdfs_corr, sigma_in_percent=sigma_in_percent, 
	ly_CDF_params=ly_CDF_params, CDF_ly_params=CDF_ly_params, ly_CDF_landau_params=ly_CDF_landau_params):
	
	"""
	It returns the light yield calculated from the energy deposit. The calculations are based 
	on the equality of the cumulative distribution functions (CDF) :
	energy => CDF(energy) => CDF(light yield) => ly

	The linear converting range 0.18 MeV < dE < 0.477 MeV corresponds 4.5 < LY < 104 ph.e.

	If energy more then 0.477 MeV the light yield calculated randomly (uniformly in the range) 
	according to the distribution

	Also a little randomness is added to the CDF value with a normal distribution and 
	standard deviation with 'sigma_in_percent' (in percent of the whole range 0 - max CDF)
	"""

	e_min, e_max = energy_range
	A, C = ly_linear_params
	if e_min < energy < e_max:
		ly_lin = A * energy + C
		cdf_raw = approx_function(ly_lin, ly_CDF_landau_params) * k_cdfs_corr
	elif e_max <= energy:
		cdf_raw = CDF_integral * np.random.uniform(0., 1.0) 
	else:
		return 0.	 
	cdf_random = random.gauss(cdf_raw, sigma_in_percent * CDF_integral)

	# Generate again while the CDF value is not in the range
	while cdf_random < 0 or cdf_random > CDF_integral:
		cdf_random = random.gauss(cdf_raw, sigma_in_percent * CDF_integral)

	return approx_function(cdf_random, CDF_ly_params)

def cluster_generator(amplitude, width, wmp, cluster_width_max=cluster_width_max, 
	chpos_min=chpos_min, chpos_max=chpos_max):

	"""
	It generates an event cluster with given weighted mean position in channels, width and 
	amplitude. 

	If right side of the cluster can be out of range, the maximum of the right side will be 
	right channel.

	At first an array [0, 0, 0, ... ] is generated which corresponds to the channels. 
	Next the cluster generated in the array. 
	Final array will be like [0, 0, ..., 1, 2, 5, 1, 0, ...], 
	[0, 17, 0, ...] or etc.
	"""

	if int(ceil(wmp + 0.5 + cluster_width_max)) < chpos_max:
		max_fired_ch = int(ceil(wmp + 0.5 + cluster_width_max))
	else:
		max_fired_ch = int(ceil(chpos_max))
	cluster = [0 for _ in range(max_fired_ch)]     
	mean = wmp
	if width == 1:
		if wmp == chpos_min:	
			fired_channel = 0
		elif wmp == chpos_max: 
			fired_channel = int(chpos_max)
		else: 
			fired_channel = int(wmp + 0.5)
		cluster[fired_channel] += amplitude	
	else:
		sigma = width * sigma_from_width
		for _ in range(amplitude):
			fired_channel = int(round(random.gauss(mean, sigma)))
			while not 0 <= fired_channel < len(cluster):
				fired_channel = int(round(random.gauss(mean, sigma)))
			cluster[fired_channel] += 1
   
	return cluster

def is_realistic(cluster, width):

	"""
	It returns TRUE if cluster is realistic: it doesn't have a gap between numders, like
	[..., 0, 1, 2, 0, 0, 5, 6, ...], and it doens't have the light yield less then width.
	"""

	cluster_only_values = [(channel, value) for channel, value in enumerate(cluster) if value > 0]
	first_channel, _ = cluster_only_values[0]
	last_channel, _ = cluster_only_values[-1]
	if len(cluster_only_values) != width or (last_channel - first_channel + 1) != width:
		return False
	else:
		return True
	
def create_cluster(amplitude, width, wmp):

	"""
	The final function for creating a signal cluster

	"""
	if wmp is False: 
		return False
	if wmp is None: 
		return False

	if not ((chpos_min < wmp) and (wmp< chpos_max)):
		return False

	if not ly_min <= amplitude >= width: return False
	shifted_wmp = wmp + 0.5 # For right counting
	cluster = cluster_generator(amplitude, width, shifted_wmp)

	# Generate again if it doesn't look like real cluster
	while is_realistic(cluster, width) is False:
		cluster = cluster_generator(amplitude, width, shifted_wmp)

	return cluster

def fcheck_wall(cluster, wmp):

	"""
	A function that prevents clusters from propagating to the gaps between the mats
	"""
 
	if (wmp + 0.5)<= firstmatgap_startch:												#1st mat
		for chann in cluster:
			if cluster[(chann + 0.5) > firstmatgap_startch] != 0.: cluster[chann] = 0. 
			return cluster
	elif firstmatgap_endch <= (wmp + 0.5)<= secmatgap_startch:							#2nd mat
		for chann in cluster:
			if (cluster[(chann + 0.5) < firstmatgap_endch] != 0.) or (cluster[(chann + 0.5) > secmatgap_startch] != 0.): cluster[chann] = 0. 
			return cluster
	elif (wmp + 0.5) >= secmatgap_endch:												#3rd mat
		for chann in cluster:
			if cluster[(chann + 0.5)< secmatgap_endch] != 0.: cluster[chann] = 0.
			return cluster
	else:
		return False																	#"False" is returned if wmp lies in the gaps

def weigthed_mean_pos(cluster):

	"""
	Calculate the weighted mean position of the cluster
	"""

	if cluster is False:
		return False
	sumup = 0.
	sumdown = 0.
	wmp = 0.
	for channel, value in enumerate(cluster):
		if value > 0:
			sumup += value * channel
			sumdown += value
	if sumdown != 0:
		wmp = sumup / sumdown - 0.5
	return wmp

#####################################################################################
#####  Class of SciFi Tracker  ######################################################
#####################################################################################

class ScifiCluster:
	# Constructor
	def __init__(self, DetID, Xraw, Yraw, Edep, Xshift=0, Yshift=0):
		self.DetID = DetID
		self.Xraw = Xraw
		self.Yraw = Yraw
		self.Edep = Edep * 1000 # to MeV
		self.ly = 0.
		self.cluster = []
		self.station = 0
		self.matnum = 0
		self.Xrec = None
		self.Yrec = None
		self.is_created = False
		# Only to check the edge events
		self.recovery_globalpos = 0
		self.delta = -13
		# The default values should be set
		self.sipm_hor_pos = +1 			  # +1 at X = +len_vert / 2 
		self.sipm_vert_pos = +1 		  #-1 at Y = -len_hor /  2
		self.is_sipm_hor_reversed = False # Channels and axis are co-directional or not
		self.is_sipm_vert_reversed = False
		self.ly_min = 4.5
		self.ly_max = 104
		self.Xshift = Xshift
		self.Yshift = Yshift

	def SetLYRange(self, ly_min, ly_max):
		self.ly_min = ly_min
		self.ly_max = ly_max

	def SetSipmPosition(self, sipm_hor_pos, sipm_vert_pos):
		self.sipm_hor_pos = sipm_hor_pos
		self.sipm_vert_pos = sipm_vert_pos
  
	def SetSipmIsReversed(self, is_sipm_hor_reversed, is_sipm_vert_reversed):
		self.is_sipm_hor_reversed = is_sipm_hor_reversed
		self.is_sipm_vert_reversed = is_sipm_vert_reversed

	# Cluster generator from the raw data. It returns False if it fails.
	def ClusterGen(self, Print = False):

		if GetMatType(self.DetID) is False:
			return False
		elif GetMatType(self.DetID) == 1: # vert
			first_coord = self.Xraw
			second_coord = self.Yraw
			sipm_pos = self.sipm_vert_pos
			is_sipm_reversed = self.is_sipm_hor_reversed
			if Print: print("Detector ID -> " + str(self.DetID) + " -> Vertical")
		elif GetMatType(self.DetID) == 0: # hor
			first_coord = self.Yraw
			second_coord = self.Xraw
			sipm_pos = self.sipm_hor_pos
			is_sipm_reversed = self.is_sipm_vert_reversed
			if Print: print("Detector ID -> " + str(self.DetID) + " -> Horizontal")
		self.matnum = GetMatNum(self.DetID)
		nmats = GetMatQty()
		matlen = GetMatLength()
		self.station = GetStationNum(self.DetID)
		if Print: print("First coordinate = " + str(first_coord))
		localpos = global_to_local(self.DetID, first_coord)
		if Print: print("Local Pos = " + str(localpos))

		if sipm_pos == +1:
			distance = GetMatLength()/2. - second_coord
		elif sipm_pos == -1:
			distance = GetMatLength()/2. + second_coord

		channelpos = cm_to_channel(localpos, reverse=is_sipm_reversed)
		
		self.ly = int(round(
						edep_to_ly(self.Edep) * ly_attenuation(distance)
					  ))

		if not self.ly_min < self.ly < self.ly_max:
			return False

		cluster_width = int(round(cluster_width_random(distance, ly=self.ly)))
		if Print: print("Cluster width: " + str(cluster_width))
		if Print: print("Channel position: " + str(channelpos))                       
		cluster = create_cluster(self.ly, cluster_width, channelpos)
		
		check_wall = fcheck_wall(cluster,channelpos)
    	#Cluster is returned if wmp is not in the 2 channels that are entirely in the mat gaps
		if check_wall!=False:
			self.is_created=True
			cluster=check_wall
		else:
			self.is_created=False
		
		wmp_of_cluster = weigthed_mean_pos(cluster)                             
		recovery_localpos = channel_to_cm(wmp_of_cluster, reverse=is_sipm_reversed)

		self.recovery_globalpos = local_to_global(self.DetID, recovery_localpos)
		if Print: print("Position readout by the SiPMs => " + str(self.recovery_globalpos))
		self.delta = first_coord - self.recovery_globalpos
		
		# Some edge events may be reconstructed incorrectly 
		if abs(self.delta) > 1:
			return False

		if GetMatType(self.DetID) == 1: # vert
			self.Xrec = self.recovery_globalpos
		elif GetMatType(self.DetID) == 0: # hor
			self.Yrec = self.recovery_globalpos	                         
	
	def GetType(self):

		if GetMatType(self.DetID) == 0:	#hor
			return 0
		else:							#vert
			return 1

	def GetNSiPMs(self):

		return GetSiPMs()               #n_sipms

	def GetXYZ(self):
		
		if self.is_created:
			return self.Xrec, self.Yrec, self.station
		else:
			return None, None, None
