import ipaddress
from urllib.parse import urlparse

from app.core.config import settings


def validate_source_url(url: str) -> str:
    """Reject non-HTTPS, credentialed, local and non-allowlisted ingestion URLs."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Source URLs must use HTTPS and include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("Source URLs cannot contain credentials")

    hostname = parsed.hostname.rstrip(".").lower()
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Private, loopback and link-local source addresses are forbidden")

    allowed = any(
        hostname == suffix or hostname.endswith(f".{suffix}")
        for suffix in settings.source_host_suffixes
    )
    if not allowed:
        raise ValueError(f"Source host is not allowlisted: {hostname}")
    return url
