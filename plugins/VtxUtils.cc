#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/StreamID.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Framework/interface/ESHandle.h"

#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/Candidate/interface/Candidate.h"

// Needed for Transient Tracks
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "MagneticField/Engine/interface/MagneticField.h"

// Needed for the kinematic fit
#include "RecoVertex/KinematicFitPrimitives/interface/TransientTrackKinematicParticle.h"
#include "RecoVertex/KinematicFitPrimitives/interface/KinematicParticleFactoryFromTransientTrack.h"
#include "RecoVertex/KinematicFit/interface/KinematicParticleVertexFitter.h"
#include "RecoVertex/KinematicFit/interface/KinematicParticleFitter.h"
#include "RecoVertex/KinematicFit/interface/MassKinematicConstraint.h"
#include "RecoVertex/KinematicFit/interface/KinematicConstrainedVertexFitter.h"
#include "RecoVertex/KinematicFit/interface/TwoTrackMassKinematicConstraint.h"

#include <iostream>

#include "VtxUtils.hh"

using namespace std;

#define _KMass_ 0.493677
#define _KMassErr_ 0.000013
#define _PiMass_ 0.13957018
#define _PiMassErr_ 0.00000035
#define _D0Mass_ 1.86484
#define _D0MassErr_ 0.00017
#define _DstMass_ 2.01027
#define _DstMassErr_ 0.00017

RefCountedKinematicTree vtxu::FitD0(const edm::EventSetup& iSetup, pat::PackedCandidate pi, pat::PackedCandidate K, bool mass_constrain, int verbose = 0) {
  // Get transient track builder
  edm::ESHandle<TransientTrackBuilder> TTBuilder;
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder",TTBuilder);

  reco::TransientTrack pi_tk = TTBuilder->build(pi.bestTrack());
  reco::TransientTrack K_tk = TTBuilder->build(K.bestTrack());

  KinematicParticleFactoryFromTransientTrack pFactory;

  std::vector<RefCountedKinematicParticle> parts;
  double chi = 0, ndf = 0;
  float mK = _KMass_, dmK = _KMass_;
  float mPi = _PiMass_, dmPi = _PiMass_;
  parts.push_back(pFactory.particle(K_tk, mK, chi, ndf, dmK));
  parts.push_back(pFactory.particle(pi_tk, mPi, chi, ndf, dmPi));

  if (!mass_constrain) {
    KinematicParticleVertexFitter VtxFitter;
    RefCountedKinematicTree D0KinTree = VtxFitter.fit(parts);
    return D0KinTree;
  }
  else {
    ParticleMass D0mass = _D0Mass_;
    MultiTrackKinematicConstraint * D0mass_c = new TwoTrackMassKinematicConstraint(D0mass);
    KinematicConstrainedVertexFitter kcVtxFitter;
    RefCountedKinematicTree D0KinTree = kcVtxFitter.fit(parts, D0mass_c);
    return D0KinTree;
  }
}

RefCountedKinematicTree vtxu::FitDst(const edm::EventSetup& iSetup, pat::PackedCandidate pisoft, pat::PackedCandidate pi, pat::PackedCandidate K, bool mass_constrain, int verbose = 0) {
  // Get the mass constrained D0
  auto D0KinTree = vtxu::FitD0(iSetup, pi, K, true);
  if(!D0KinTree->isValid()) return D0KinTree;
  D0KinTree->movePointerToTheTop();
  auto D0_reco = D0KinTree->currentParticle();

  // Get transient track builder
  edm::ESHandle<TransientTrackBuilder> TTBuilder;
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder",TTBuilder);

  reco::TransientTrack pisoft_tk = TTBuilder->build(pisoft.bestTrack());

  KinematicParticleFactoryFromTransientTrack pFactory;

  std::vector<RefCountedKinematicParticle> parts;
  double chi = 0, ndf = 0;
  float mPi = _PiMass_, dmPi = _PiMass_;
  parts.push_back(D0_reco);
  parts.push_back(pFactory.particle(pisoft_tk, mPi, chi, ndf, dmPi));

  if (!mass_constrain) {
    KinematicParticleVertexFitter VtxFitter;
    RefCountedKinematicTree DstKinTree = VtxFitter.fit(parts);
    return DstKinTree;
  }
  else {
    ParticleMass Dstmass = _DstMass_;
    MultiTrackKinematicConstraint * Dstmass_c = new TwoTrackMassKinematicConstraint(Dstmass);
    KinematicConstrainedVertexFitter kcVtxFitter;
    RefCountedKinematicTree DstKinTree = kcVtxFitter.fit(parts, Dstmass_c);
    return DstKinTree;
  }
}

double vtxu::computeDCA(const edm::EventSetup& iSetup, pat::PackedCandidate cand, GlobalPoint p) {
  // Get transient track builder
  edm::ESHandle<TransientTrackBuilder> TTBuilder;
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder",TTBuilder);

  reco::TransientTrack tk = TTBuilder->build(cand.bestTrack());

  TrajectoryStateClosestToPoint theDCAXBS = tk.trajectoryStateClosestToPoint(p);
  double DCA = theDCAXBS.perigeeParameters().transverseImpactParameter();
  // double DCABSErr = theDCAXBS.perigeeError().transverseImpactParameterError();
  // pair<double,double> DCA = make_pair(DCABS,DCABSErr);
  return DCA;
}

TLorentzVector vtxu::getTLVfromKinPart(ReferenceCountingPointer<KinematicParticle> p) {
  auto pvec = p->currentState().globalMomentum();
  auto mass = p->currentState().mass();
  TLorentzVector out;
  out.SetXYZM(pvec.x(), pvec.y(), pvec.z(), mass);
  return out;
}


TLorentzVector vtxu::getTLVfromTrack(reco::Track t, double mass) {
  TLorentzVector out;
  auto p3 = t.momentum();
  auto pt = sqrt(p3.perp2());
  out.SetPtEtaPhiM(pt, p3.eta(), p3.phi(), mass);
  return out;
}

TLorentzVector vtxu::getTLVfromCand(pat::PackedCandidate p, double mass) {
  TLorentzVector out;
  out.SetPtEtaPhiM(p.pt(), p.eta(), p.phi(), mass);
  return out;
}
