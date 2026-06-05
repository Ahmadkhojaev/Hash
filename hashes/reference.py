"""
Taqqoslash uchun standart (og'ir vaznli) xesh funksiyalar.

Yengil vaznli Ascon-Hash bilan solishtirish maqsadida Python'ning ichki
`hashlib` kutubxonasidagi keng tarqalgan xesh funksiyalari ishlatiladi.
Bu funksiyalar barchasi bytes qabul qilib, bytes (digest) qaytaradi -
shu tarzda ular Ascon bilan bir xil interfeysga ega bo'ladi.
"""

import hashlib


def sha256(message: bytes) -> bytes:
    """SHA-256 (256-bit) - keng tarqalgan standart xesh funksiya."""
    return hashlib.sha256(message).digest()


def sha3_256(message: bytes) -> bytes:
    """SHA-3-256 (Keccak asosidagi NIST standarti, 256-bit)."""
    return hashlib.sha3_256(message).digest()


def blake2s(message: bytes) -> bytes:
    """BLAKE2s (256-bit) - tez va zamonaviy xesh funksiya."""
    return hashlib.blake2s(message).digest()
