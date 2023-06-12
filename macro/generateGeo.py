from array import array
import logging
import ROOT as r


def generate_geo(geofile, params):
    f = r.TFile.Open(geofile, 'recreate')
    parray = r.TVectorD(len(params), array('d', params))
    parray.Write('params')
    f.Close()
    logging.info('Geofile constructed at ' + geofile)
    return geofile