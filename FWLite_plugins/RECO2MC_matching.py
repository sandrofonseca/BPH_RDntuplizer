import ROOT as rt
import numpy as np
import re
# load FWLite C++ libraries
rt.gSystem.Load("libFWCoreFWLite.so");
rt.gSystem.Load("libDataFormatsFWLite.so");
rt.FWLiteEnabler.enable()

# load FWlite python libraries
from DataFormats.FWLite import Handle

handle = {}
handle['PFCand'] = [Handle('vector<pat::PackedCandidate>'), 'packedPFCandidates']
handle['Muons'] = [Handle('std::vector<pat::Muon>'), 'slimmedMuons']
handle['Vtxs'] = [Handle('vector<reco::Vertex>'), 'offlineSlimmedPrimaryVertices']

def print_candidate(p, addon=''):
    print addon+'Pt: {:.2f} Eta: {:.2f} Phi: {:.2f}'.format(p.pt(), p.eta(), p.phi())

def deltaR(p1, p2):
    return np.hypot(p1.phi()-p2.phi(), p1.eta()-p2.eta())

def matchRECO2MC(p_MC, reco_collection):
    p_best = None
    dR_best = -1
    dpt_best = 0

    for p in reco_collection:
        if p.charge() == p_MC.charge():
            dR = deltaR(p, p_MC)
            dpt = (p.pt() - p_MC.pt())/ p_MC.pt()
            if (p_best is None) or dR < dR_best or (abs(dR-dR_best) < 1e-3 and dpt < dpt_best):
                p_best = p
                dR_best = dR
                dpt_best = dpt

    return [p_best, dR_best, dpt_best]

def addToOutput(p, tag, outmap):
    outmap[tag+'_pt'] = p.pt()
    outmap[tag+'_eta'] = p.eta()
    outmap[tag+'_phi'] = p.phi()
    outmap[tag+'_pdgId'] = p.pdgId()
    outmap[tag+'_dz'] = p.dz()
    outmap[tag+'_dxy'] = p.dxy()

    if p.hasTrackDetails():
        outmap[tag+'_dzError'] = p.dzError()
        outmap[tag+'_dxyError'] = p.dxyError()
        t = p.bestTrack()
        outmap[tag+'_Nchi2'] = t.normalizedChi2()
        outmap[tag+'_chi2'] = t.chi2()
        outmap[tag+'_ndof'] = t.ndof()
        outmap[tag+'_Nhits'] = t.numberOfValidHits()
    else:
        outmap[tag+'_dzError'] = -1
        outmap[tag+'_dxyError'] = -1
        outmap[tag+'_Nchi2'] = -1
        outmap[tag+'_chi2'] = -1
        outmap[tag+'_ndof'] = -1
        outmap[tag+'_Nhits'] = -1


class RECO2MC_matching:
    def __init__(self,
                 verbose=False
                ):
        self.verbose = verbose

    def process(self, event, output, verbose):
        out = output.evt_out

        prods = {}
        for k,v in handle.iteritems():
            event.getByLabel(v[1], v[0])
            prods[k] = v[0].product()

        if verbose or self.verbose:
            print '------- Matching MC to RECO ---------'

        event.RECO_MCmatch = {}
        for n, p_MC in event.MC_part.iteritems():
            m = None
            if 'mu' in n:
                # m = matchRECO2MC(p_MC, prods['Muons'])
                m = matchRECO2MC(p_MC, prods['PFCand'])
                if not m[0] is None:
                    out['muReco_pdgId'] = m[0].pdgId()
                    out['muReco_isMuon'] = m[0].isMuon()
                    out['muReco_isCaloMuon'] = m[0].isCaloMuon()
                    out['muReco_isTrackerMuon'] = m[0].isTrackerMuon()
                    out['muReco_isStandAloneMuon'] = m[0].isStandAloneMuon()
                    out['muReco_isGlobalMuon'] = m[0].isGlobalMuon()

                    out['muReco_isTightMuon'] = -1
                    out['muReco_isSoftMuon'] = -1
                    out['muReco_isLooseMuon'] = -1
                    out['muReco_isMediumMuon'] = -1
                    for mu in prods['Muons']:
                        c = np.abs(mu.pt() - m[0].pt())/mu.pt() < 5e-3
                        c *= np.abs(mu.eta() - m[0].eta())/mu.eta() < 5e-3
                        c *= np.abs(mu.phi() - m[0].phi())/mu.phi() < 5e-3
                        if c:
                            out['muReco_isLooseMuon'] = mu.isLooseMuon()
                            out['muReco_isMediumMuon'] = mu.isMediumMuon()
                            for v in prods['Vtxs']:
                                if mu.isTightMuon(v):
                                    out['muReco_isTightMuon'] = mu.isTightMuon(v)
                                if mu.isSoftMuon(v):
                                    out['muReco_isSoftMuon'] = mu.isSoftMuon(v)
            elif abs(p_MC.pdgId()) in [211, 321]:
                m = matchRECO2MC(p_MC, prods['PFCand'])

            if not m is None:
                if not m[0] is None:
                    event.RECO_MCmatch[n] = m
                    addToOutput(m[0], n+'Reco', out)
                    out[n+'_RecoMC_dR'] = m[1]
                    out[n+'_RecoMC_dpt'] = m[2]
                    if verbose or self.verbose:
                        print '{}: dR={:1.1e} dpt={:1.1e}'.format(n, m[1], m[2])
                        print_candidate(p_MC, '\t')
                        print_candidate(m[0], '\t')


        return True
