"""
Ascon-Hash256 implementatsiyasi (Ascon v1.2).

Ascon - NIST tomonidan 2023-yilda yengil vaznli (lightweight) kriptografiya
standarti sifatida tanlangan algoritmlar oilasi. Ushbu modul Ascon-Hash
(256-bitli xesh) ni toza Python'da, ta'lim maqsadida o'qilishi oson tarzda
amalga oshiradi.

Tuzilishi (sponge konstruksiyasi):
    1. Initsializatsiya  - boshlang'ich holatni IV bilan to'ldirish + p^12
    2. Absorbing (yutish) - xabarni 64-bitli bloklar bilan yutish
    3. Squeezing (siqib chiqarish) - 256-bitli xesh qiymatini chiqarish

Manba spetsifikatsiyasi: https://ascon.iaik.tugraz.at
"""

# 64-bitli so'zlar bilan ishlash uchun niqob (mask)
MASK64 = 0xFFFFFFFFFFFFFFFF

# p^12 permutatsiyasi uchun raund konstantalari (12 ta raund)
ROUND_CONSTANTS = [
    0xf0, 0xe1, 0xd2, 0xc3,
    0xb4, 0xa5, 0x96, 0x87,
    0x78, 0x69, 0x5a, 0x4b,
]

# Ascon-Hash uchun boshlang'ich qiymat (IV)
# Format: r(8) || a(12) || a-b(0) || h(256 bit chiqish)
IV_HASH = 0x00400c0000000100

# Sponge konstruksiyasining "rate" qiymati (baytlarda) = 64 bit
RATE = 8


def _rotr(x: int, n: int) -> int:
    """64-bitli so'zni o'ngga aylantirish (rotate right)."""
    return ((x >> n) | (x << (64 - n))) & MASK64


def _permutation(state: list, rounds: int) -> None:
    """
    Ascon permutatsiyasi p^rounds.

    state - 5 ta 64-bitli so'zdan iborat ro'yxat [x0, x1, x2, x3, x4].
    Permutatsiya 3 qatlamdan iborat: konstanta qo'shish, S-box, chiziqli diffuziya.
    """
    x0, x1, x2, x3, x4 = state

    # p^12 uchun konstantalar oxiridan boshlanadi (12-rounds => indeks 0)
    for c in ROUND_CONSTANTS[12 - rounds:]:
        # --- 1. Konstanta qo'shish qatlami (addition of round constant) ---
        x2 ^= c

        # --- 2. O'rin almashtirish qatlami (substitution layer, 5-bit S-box) ---
        x0 ^= x4
        x4 ^= x3
        x2 ^= x1
        t0 = (x0 ^ MASK64) & x1
        t1 = (x1 ^ MASK64) & x2
        t2 = (x2 ^ MASK64) & x3
        t3 = (x3 ^ MASK64) & x4
        t4 = (x4 ^ MASK64) & x0
        x0 ^= t1
        x1 ^= t2
        x2 ^= t3
        x3 ^= t4
        x4 ^= t0
        x1 ^= x0
        x0 ^= x4
        x3 ^= x2
        x2 ^= MASK64  # ya'ni x2 = ~x2

        # --- 3. Chiziqli diffuziya qatlami (linear diffusion layer) ---
        x0 ^= _rotr(x0, 19) ^ _rotr(x0, 28)
        x1 ^= _rotr(x1, 61) ^ _rotr(x1, 39)
        x2 ^= _rotr(x2, 1) ^ _rotr(x2, 6)
        x3 ^= _rotr(x3, 10) ^ _rotr(x3, 17)
        x4 ^= _rotr(x4, 7) ^ _rotr(x4, 41)

    state[0], state[1], state[2], state[3], state[4] = x0, x1, x2, x3, x4


def ascon_hash(message: bytes) -> bytes:
    """
    Berilgan xabardan 256-bitli (32 baytli) Ascon-Hash qiymatini hisoblaydi.

    Parametr:
        message - xesh qilinadigan kirish baytlari.
    Qaytaradi:
        32 baytli xesh qiymati (bytes).
    """
    # --- 1. Initsializatsiya ---
    state = [IV_HASH, 0, 0, 0, 0]
    _permutation(state, 12)

    # --- 2. Absorbing (10* padding bilan) ---
    # Xabarga 0x80 bayti qo'shilib, blok to'lguncha 0 lar bilan to'ldiriladi.
    padded = message + b"\x80"
    while len(padded) % RATE != 0:
        padded += b"\x00"

    for i in range(0, len(padded), RATE):
        block = int.from_bytes(padded[i:i + RATE], "big")
        state[0] ^= block
        _permutation(state, 12)

    # --- 3. Squeezing ---
    output = b""
    while len(output) < 32:
        output += state[0].to_bytes(8, "big")
        if len(output) < 32:
            _permutation(state, 12)

    return output[:32]


def ascon_hash_hex(message: bytes) -> str:
    """Ascon-Hash natijasini o'n oltilik (hex) satr ko'rinishida qaytaradi."""
    return ascon_hash(message).hex()


if __name__ == "__main__":
    # O'zini-tekshirish: bo'sh xabar uchun ma'lum test vektori (Ascon v1.2)
    EXPECTED_EMPTY = (
        "7346bc14f036e87ae03d0997913088f5f68411434b3cf8b54fa796a80d251f91"
    )
    result = ascon_hash_hex(b"")
    print("Bo'sh xabar xeshi:", result)
    print("Kutilgan qiymat :", EXPECTED_EMPTY)
    print("Mos keladimi    :", result == EXPECTED_EMPTY)
