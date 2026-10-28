"""Pluggable signing for the floor's register (E1) and authority chains (E7).

The reference uses symmetric HMAC-SHA256 and names it that way in the compass: the point is
that principals' keys stay out of agents' reach, not which algorithm is used. A deployment
that wants asymmetric signatures - so verifiers only ever see public keys, and signing keys
sit in an HSM or a separate signer service - can pass a Signer in place of the raw key
bytes anywhere `sign_link`, `sign_entry`, `Floor(governor_keys=...)` or
`verify_chain(keys=...)` currently take bytes.

A Signer is any object with these two methods:
    sign(body: bytes) -> str
    verify(body: bytes, signature: str) -> bool

The signature is a text token the library stores and compares verbatim; its internal
structure (hex, base64, structured, etc.) is the signer's business. compasskit ships one
reference implementation, `HmacSigner`, and leaves asymmetric algorithms to the caller so
the package stays standard-library only.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Union


class HmacSigner(object):
    """The reference HMAC-SHA256 signer: symmetric, stdlib-only.

    Equivalent to the bytes-key path that `sign_link`, `sign_entry` and `verify_chain`
    accept directly; passing `HmacSigner(key)` is identical in behaviour to passing `key`.
    """

    __slots__ = ("_key",)

    def __init__(self, key):
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("HmacSigner needs a bytes key, got %s" % type(key).__name__)
        if not key:
            raise ValueError("HmacSigner needs a non-empty key")
        self._key = bytes(key)

    def sign(self, body):
        if not isinstance(body, (bytes, bytearray)):
            raise TypeError("sign(body) needs bytes, got %s" % type(body).__name__)
        return hmac.new(self._key, bytes(body), hashlib.sha256).hexdigest()

    def verify(self, body, signature):
        if not isinstance(signature, str):
            return False
        try:
            expected = self.sign(body)
        except TypeError:
            return False
        return hmac.compare_digest(expected, signature)


KeyLike = Union[bytes, bytearray, "object"]


def coerce_signer(obj):
    """Return a Signer. Raw bytes are wrapped in the reference `HmacSigner`.

    Any object exposing callable `sign` and `verify` attributes is returned as-is. Anything
    else raises TypeError - a deployment that calls into compasskit with an opaque config
    object by mistake should fail loudly, not fall through to a signature that nothing can
    verify.
    """
    if isinstance(obj, (bytes, bytearray)):
        return HmacSigner(bytes(obj))
    sign = getattr(obj, "sign", None)
    verify = getattr(obj, "verify", None)
    if callable(sign) and callable(verify):
        return obj
    raise TypeError(
        "expected bytes or a Signer with callable .sign and .verify, got %s"
        % type(obj).__name__
    )
