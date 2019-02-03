import ROOT as rt
import numpy as np
import re
# load FWLite C++ libraries
rt.gSystem.Load("libFWCoreFWLite.so");
rt.gSystem.Load("libDataFormatsFWLite.so");
rt.FWLiteEnabler.enable()

from pdg_utils import getMass

def getTLorenzVector(p, verbose=0):
    if verbose:
        print 'PtEtaPhiM:{:.3f}, {:.3f}, {:.3f}, {:.4f}'.format(p.pt(), p.eta(), p.phi(), p.mass())
    out =  rt.TLorentzVector()
    out.SetPtEtaPhiM(p.pt(), p.eta(), p.phi(), p.mass())
    return out

def addP4ToOutput(p, tag, outmap):
    outmap[tag+'_pt'] = p.Pt()
    outmap[tag+'_eta'] = p.Eta()
    outmap[tag+'_phi'] = p.Phi()
    outmap[tag+'_pdgId'] = p.M()


class EasyRecoQuantities:
    def __init__(self,
                 verbose=False
                ):
        self.verbose = verbose

    def process(self, event, output, verbose):
        out = output.evt_out

        if verbose or self.verbose:
            print '------- Easy RECO Quantities ---------'

        p4_D0_RECO = getTLorenzVector(event.RECO_MCmatch['K'][0]) + getTLorenzVector(event.RECO_MCmatch['pi'][0])
        addP4ToOutput(p4_D0_RECO, 'D0_RECO', out)
        p4_Dst_RECO = p4_D0_RECO + getTLorenzVector(event.RECO_MCmatch['pisoft'][0])
        addP4ToOutput(p4_Dst_RECO, 'Dst_RECO', out)
        p4_vis_RECO = p4_Dst_RECO + getTLorenzVector(event.RECO_MCmatch['mu'][0])

        out['M_vis_RECO'] = p4_vis_RECO.M()

        pz_B_RECO = p4_vis_RECO.Pz() * getMass(511) / p4_vis_RECO.M()
        B_vect = event.d_flightB_MC * ( pz_B_RECO / event.d_flightB_MC.z() )
        p4_B_RECO = rt.TLorentzVector()
        p4_B_RECO.SetVectM(B_vect, getMass(511))
        addP4ToOutput(p4_B_RECO, 'B_RECO', out)

        out['q2_RECO'] = (p4_B_RECO - p4_Dst_RECO).M2()

        return True