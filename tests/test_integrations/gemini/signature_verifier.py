"""Synthetic verifier copied from Core test support; never used for live effects."""

from zeo_core.contracts.connections import EffectAuthorization


class AcceptingSignatureVerifier:
    def verify_signature(self, authorization: EffectAuthorization) -> bool:
        del authorization
        return True
