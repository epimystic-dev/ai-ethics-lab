"""Tests for compasskit.signing and its plug-in use by authority and floor.

The signing module exists so a deployment can plug an asymmetric signer (keys in an HSM,
verifiers holding only public keys) into the same slots that accept the reference HMAC
bytes. These tests cover (a) the HmacSigner round-trip, (b) coerce_signer's acceptance
rules, and (c) end-to-end use of a non-HMAC signer through sign_link / verify_chain /
sign_entry / Floor.apply. The non-HMAC signer here is a keyed BLAKE2b with a distinct
output prefix - it stands in for any user-supplied Signer; the point is that compasskit
only calls .sign and .verify, so the algorithm is interchangeable.
"""

from __future__ import annotations

import hashlib
import unittest

from compasskit.authority import sign_link, verify_chain
from compasskit.floor import Floor, RegisterError, sign_entry
from compasskit.signing import HmacSigner, coerce_signer


class Blake2bSigner(object):
    """A deliberately not-HMAC-SHA256 Signer used to prove the slot is pluggable.

    Prefixes signatures with 'b2:' so a round-trip against an HmacSigner would fail: this
    stops a test from passing by accident when both ends happen to agree on HMAC.
    """

    def __init__(self, key):
        self._key = key

    def sign(self, body):
        return "b2:" + hashlib.blake2b(body, key=self._key, digest_size=32).hexdigest()

    def verify(self, body, signature):
        if not isinstance(signature, str) or not signature.startswith("b2:"):
            return False
        return signature == self.sign(body)


class _RejectAllSigner(object):
    """A signer whose verify always returns False - used to prove verification is called."""

    def sign(self, body):
        return "no"

    def verify(self, body, signature):
        return False


class HmacSignerBasics(unittest.TestCase):
    def test_round_trip(self):
        s = HmacSigner(b"a-key")
        sig = s.sign(b"hello")
        self.assertTrue(s.verify(b"hello", sig))

    def test_verify_rejects_tampered_body(self):
        s = HmacSigner(b"a-key")
        sig = s.sign(b"hello")
        self.assertFalse(s.verify(b"hell0", sig))

    def test_verify_rejects_tampered_signature(self):
        s = HmacSigner(b"a-key")
        sig = s.sign(b"hello")
        self.assertFalse(s.verify(b"hello", sig[:-1] + ("0" if sig[-1] != "0" else "1")))

    def test_verify_rejects_non_string_signature(self):
        self.assertFalse(HmacSigner(b"a-key").verify(b"hello", 1234))

    def test_rejects_empty_key(self):
        with self.assertRaises(ValueError):
            HmacSigner(b"")

    def test_rejects_non_bytes_key(self):
        with self.assertRaises(TypeError):
            HmacSigner("a-key")

    def test_sign_rejects_non_bytes_body(self):
        with self.assertRaises(TypeError):
            HmacSigner(b"a-key").sign("hello")

    def test_two_signers_with_different_keys_disagree(self):
        a = HmacSigner(b"a")
        b = HmacSigner(b"b")
        self.assertFalse(b.verify(b"hello", a.sign(b"hello")))


class CoerceSigner(unittest.TestCase):
    def test_bytes_becomes_hmac_signer(self):
        s = coerce_signer(b"a-key")
        self.assertIsInstance(s, HmacSigner)
        self.assertTrue(s.verify(b"x", s.sign(b"x")))

    def test_bytearray_becomes_hmac_signer(self):
        s = coerce_signer(bytearray(b"a-key"))
        self.assertIsInstance(s, HmacSigner)

    def test_signer_object_passes_through(self):
        src = Blake2bSigner(b"a-key")
        self.assertIs(coerce_signer(src), src)

    def test_rejects_bare_object(self):
        with self.assertRaises(TypeError):
            coerce_signer(object())

    def test_rejects_object_with_only_sign(self):
        obj = type("X", (), {"sign": lambda self, b: ""})()
        with self.assertRaises(TypeError):
            coerce_signer(obj)

    def test_rejects_string_key(self):
        with self.assertRaises(TypeError):
            coerce_signer("a-key")

    def test_rejects_none(self):
        with self.assertRaises(TypeError):
            coerce_signer(None)


KEYS_HMAC = {"ops lead": b"principal-key"}
HUMANS = {"ops lead"}


class ChainsWithPluggableSigner(unittest.TestCase):
    """E7 (1): the same chain rules apply whether the signer is HMAC or something else."""

    def test_sign_link_accepts_signer_object(self):
        signer = Blake2bSigner(b"principal-key")
        link = sign_link(signer, "ops lead", "agent-a", "review")
        self.assertTrue(link["signature"].startswith("b2:"))
        chk = verify_chain([link], keys={"ops lead": signer}, humans=HUMANS, agent="agent-a", action="review")
        self.assertTrue(chk.ok, chk.reason)

    def test_signer_mismatch_fails_verification(self):
        link = sign_link(Blake2bSigner(b"principal-key"), "ops lead", "agent-a", "review")
        chk = verify_chain([link], keys={"ops lead": b"principal-key"}, humans=HUMANS, agent="agent-a")
        self.assertFalse(chk.ok)
        self.assertIn("signature", chk.reason)

    def test_mixed_bytes_and_signer_in_keys_map(self):
        """One principal uses bytes, another uses a Signer; the chain still verifies."""
        p_signer = Blake2bSigner(b"principal-key")
        a_bytes = b"agent-a-key"
        chain = [
            sign_link(p_signer, "ops lead", "agent-a", "review, comment"),
            sign_link(a_bytes, "agent-a", "agent-b", "review"),
        ]
        chk = verify_chain(
            chain,
            keys={"ops lead": p_signer, "agent-a": a_bytes},
            humans=HUMANS,
            agent="agent-b",
            allow_agent_delegation=True,
        )
        self.assertTrue(chk.ok, chk.reason)

    def test_reject_all_signer_actually_rejects(self):
        """Prove verify is invoked by making it return False and watching the chain fail."""
        link = sign_link(b"ops-key", "ops lead", "agent-a", "review")
        chk = verify_chain([link], keys={"ops lead": _RejectAllSigner()}, humans=HUMANS, agent="agent-a")
        self.assertFalse(chk.ok)
        self.assertIn("does not verify", chk.reason)

    def test_hmac_signer_equivalent_to_raw_bytes(self):
        """Passing HmacSigner(k) is identical to passing k."""
        a = sign_link(b"principal-key", "ops lead", "agent-a", "review")
        b = sign_link(HmacSigner(b"principal-key"), "ops lead", "agent-a", "review")
        self.assertEqual(a["signature"], b["signature"])


class FloorRegisterWithPluggableSigner(unittest.TestCase):
    """E1: the floor register's governor signatures are also pluggable."""

    def _entry(self, signer_or_key):
        e = {
            "id": "FR-plug-1", "restraint": "self_restraint", "act": "exception", "class": "D",
            "governor": "head of security", "reason": "supervised migration",
            "scope": "stop_service", "decided_at": "2026-10-28T09:00:00Z",
            "expires_or_review": "2026-11-28",
        }
        e["signature"] = sign_entry(signer_or_key, e)
        return e

    def test_floor_accepts_signer_object_governor(self):
        signer = Blake2bSigner(b"gov-key")
        f = Floor(governor_keys={"head of security": signer})
        entry = self._entry(signer)
        f.apply(entry)
        self.assertEqual(len(f.register), 1)
        self.assertTrue(entry["signature"].startswith("b2:"))

    def test_floor_signer_mismatch_rejected(self):
        """A register entry signed by one algorithm is rejected under another."""
        f = Floor(governor_keys={"head of security": b"gov-key"})
        entry = self._entry(Blake2bSigner(b"gov-key"))
        with self.assertRaises(RegisterError):
            f.apply(entry)

    def test_floor_mixed_governors_bytes_and_signer(self):
        """One governor uses bytes, another uses a Signer; both can file register entries."""
        signer = Blake2bSigner(b"ciso-key")
        f = Floor(governor_keys={"head of security": b"gov-key", "ciso": signer})
        e1 = self._entry(b"gov-key")
        f.apply(e1)
        e2 = {
            "id": "FR-plug-2", "restraint": "self_restraint", "act": "exception", "class": "D",
            "governor": "ciso", "reason": "scheduled maintenance", "scope": "stop_service",
            "decided_at": "2026-10-28T10:00:00Z", "expires_or_review": "2026-11-28",
        }
        e2["signature"] = sign_entry(signer, e2)
        f.apply(e2)
        self.assertEqual([x["id"] for x in f.register], ["FR-plug-1", "FR-plug-2"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
