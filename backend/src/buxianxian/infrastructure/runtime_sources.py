"""Production-only entropy and opaque identifier sources for new-game drafts."""

import secrets

from buxianxian.infrastructure.random_source import XorShift64StarRandom


class SecureXorShift64StarFactory:
    """Seed a fresh persistent game RNG from operating-system entropy."""

    def create(self) -> XorShift64StarRandom:
        """Return a new nonzero xorshift64star v1 source."""

        seed = secrets.randbits(64)
        return XorShift64StarRandom.from_seed(seed or 1)


class SecureDraftIdentifierSource:
    """Create unpredictable identifiers outside the deterministic game RNG."""

    def create(self) -> str:
        """Return a URL-safe opaque draft identifier."""

        return secrets.token_urlsafe(24)
