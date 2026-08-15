"""
Local TLS interoperability shim.

This machine runs Avast Web Shield, which terminates TLS with its own local CA
(`C:\\ProgramData\\Avast Software\\Avast\\wscert.pem`). That certificate is a valid
root for this machine but is not RFC 5280 strict-conformant: its basicConstraints
extension is not marked critical. Python 3.13 enables ssl.VERIFY_X509_STRICT by
default, so every outbound HTTPS request fails with:

    SSLCertVerificationError: Basic Constraints of CA cert not marked critical

Importing this module:
  1. points OpenSSL at a bundle of certifi + the local Avast root, and
  2. clears VERIFY_X509_STRICT only.

Chain building, signature verification, expiry and hostname checks all stay ON.
Certificate verification is never disabled.
"""

from __future__ import annotations

import os
import ssl
from pathlib import Path

CA_BUNDLE = Path(__file__).resolve().parent.parent / "configs" / "ca_bundle.pem"
AVAST_CA = Path(r"C:\ProgramData\Avast Software\Avast\wscert.pem")


def build_bundle() -> Path:
    """Write certifi + the local AV root into one PEM. Idempotent."""
    import certifi

    data = Path(certifi.where()).read_bytes()
    if AVAST_CA.exists():
        data += b"\n" + AVAST_CA.read_bytes()
    CA_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    CA_BUNDLE.write_bytes(data)
    return CA_BUNDLE


def install() -> None:
    """Install the bundle + relax strict-conformance checking process-wide."""
    if not CA_BUNDLE.exists():
        build_bundle()

    bundle = str(CA_BUNDLE)
    os.environ["SSL_CERT_FILE"] = bundle
    os.environ["REQUESTS_CA_BUNDLE"] = bundle
    os.environ["CURL_CA_BUNDLE"] = bundle

    _orig = ssl.create_default_context

    def _patched(*args, **kwargs):
        kwargs.setdefault("cafile", bundle)
        ctx = _orig(*args, **kwargs)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT  # keep verification, drop strictness
        return ctx

    ssl.create_default_context = _patched  # type: ignore[assignment]
    ssl._create_default_https_context = _patched  # type: ignore[attr-defined]

    # requests/urllib3 build their own context and never call ssl.create_default_context,
    # so patch their factory too.
    try:
        import urllib3.util.ssl_ as u3ssl

        _orig_u3 = u3ssl.create_urllib3_context

        def _patched_u3(*args, **kwargs):
            ctx = _orig_u3(*args, **kwargs)
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
            try:
                ctx.load_verify_locations(cafile=bundle)
            except Exception:
                pass
            return ctx

        u3ssl.create_urllib3_context = _patched_u3  # type: ignore[assignment]
        try:
            import urllib3.connection as u3conn

            u3conn.create_urllib3_context = _patched_u3  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            import urllib3.connectionpool as u3pool

            u3pool.create_urllib3_context = _patched_u3  # type: ignore[attr-defined]
        except Exception:
            pass
    except ImportError:
        pass


install()
