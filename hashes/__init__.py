"""Yengil vaznli xesh funksiyalar to'plami va taqqoslash funksiyalari."""

from .ascon_hash import ascon_hash, ascon_hash_hex
from .reference import sha256, sha3_256, blake2s
from .photon import photon_beetle_hash, photon_beetle_hash_hex
from .spongent import spongent_hash, spongent_hash_hex, SPONGENT_128


def _spongent128(message: bytes) -> bytes:
    """SPONGENT-128 (registr uchun standart interfeys)."""
    return spongent_hash(message, SPONGENT_128)


# Dasturda ishlatiladigan barcha xesh funksiyalar registri.
# Kalit - foydalanuvchiga ko'rsatiladigan nom, qiymat - (funksiya, turi).
# "turi": "yengil" (lightweight) yoki "standart" (taqqoslash uchun).
HASH_REGISTRY = {
    "Ascon-Hash256": (ascon_hash, "yengil"),
    "PHOTON-Beetle": (photon_beetle_hash, "yengil"),
    "SPONGENT-128": (_spongent128, "yengil"),
    "SHA-256": (sha256, "standart"),
    "SHA-3-256": (sha3_256, "standart"),
    "BLAKE2s": (blake2s, "standart"),
}

__all__ = [
    "ascon_hash",
    "ascon_hash_hex",
    "photon_beetle_hash",
    "photon_beetle_hash_hex",
    "spongent_hash",
    "spongent_hash_hex",
    "SPONGENT_128",
    "sha256",
    "sha3_256",
    "blake2s",
    "HASH_REGISTRY",
]
