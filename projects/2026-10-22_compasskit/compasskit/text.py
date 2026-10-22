"""Console-safe text.

The compass carries Sanskrit terms in IAST, with diacritics. A console on a legacy code page
cannot encode them, and echoing them raw would crash a report mid-write. For terminal output
this module folds IAST to plain ASCII ("pramana" for the term with long a and retroflex n),
which keeps the word readable. Anything that does not fold is shown as <U+XXXX>. JSON output
is escaped by the encoder instead, and files are written as UTF-8 with diacritics intact.
"""

from __future__ import annotations

import unicodedata


def fold(text: str) -> str:
    """Return printable ASCII: diacritics dropped, anything else made visible as <U+XXXX>."""
    out = []
    for ch in unicodedata.normalize("NFKD", text):
        cp = ord(ch)
        if 32 <= cp < 127 or ch in "\n\t":
            out.append(ch)
        elif unicodedata.combining(ch):
            continue
        else:
            out.append("<U+%04X>" % cp)
    return "".join(out)
