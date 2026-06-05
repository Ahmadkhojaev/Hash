"""
SPONGENT yengil vaznli xesh funksiyasi implementatsiyasi.

SPONGENT - A. Bogdanov va boshqalar tomonidan ishlab chiqilgan, PRESENT
tipidagi permutatsiya asosidagi sponge konstruksiyasidan foydalanadigan
yengil vaznli xesh funksiyalar oilasi (ISO/IEC 29192-5 standarti). U 88, 128,
160, 224 va 256 bitli xesh o'lchamlarini qo'llab-quvvatlaydi.

Ushbu modul rasmiy (public domain) C++ reference implementatsiyasiga aniq
asoslangan holda toza Python'da amalga oshirilgan va rasmiy test vektoriga
tekshirilgan.

Permutatsiyaning har bir raundi 3 qadamdan iborat:
    1. Hisoblagich (LFSR) qiymatlarini holatga qo'shish
    2. sBoxLayer - har bir baytga 4-bitli S-box qo'llash
    3. pLayer   - bitlarni qayta joylashtirish (PRESENT tipidagi)

Manba: https://sites.google.com/site/spongenthash/
"""

# SPONGENT 4-bitli S-box
S = [0xe, 0xd, 0xb, 0x0, 0x2, 0x1, 0x4, 0xf,
     0x7, 0xa, 0x8, 0x5, 0x9, 0xc, 0x3, 0x6]


def _build_sbox_layer():
    """4-bitli S-box'dan 8-bitli (bayt uchun) S-box jadvalini quradi."""
    table = [0] * 256
    for x in range(256):
        table[x] = (S[(x >> 4) & 0xF] << 4) | S[x & 0xF]
    return table


SBOX_LAYER = _build_sbox_layer()


class SpongentParams:
    """SPONGENT variantining parametrlari."""

    def __init__(self, rate, capacity, hashsize, n_rounds, version, iv):
        self.rate = rate
        self.capacity = capacity
        self.hashsize = hashsize
        self.n_rounds = n_rounds
        self.version = version
        self.iv = iv
        self.n_bits = capacity + rate          # holatning umumiy bit hajmi
        self.n_sbox = self.n_bits // 8         # holatning bayt hajmi
        self.r_bytes = rate // 8               # bir blokdagi baytlar soni


# Standart SPONGENT variantlari
SPONGENT_88 = SpongentParams(8, 80, 88, 45, 88808, 0x05)
SPONGENT_128 = SpongentParams(8, 128, 128, 70, 1281288, 0x7A)
SPONGENT_256 = SpongentParams(16, 256, 256, 140, 25625616, 0x9E)


def _l_counter(lfsr, version):
    """LFSR hisoblagichni bir qadam oldinga suradi (variantga bog'liq)."""
    if version == 88808:
        lfsr = (lfsr << 1) | (((0x20 & lfsr) >> 5) ^ ((0x10 & lfsr) >> 4))
        lfsr &= 0x3F
    elif version in (1281288, 16016016, 16016080, 22422416):
        lfsr = (lfsr << 1) | (((0x40 & lfsr) >> 6) ^ ((0x20 & lfsr) >> 5))
        lfsr &= 0x7F
    elif version in (8817688, 128256128, 160320160, 224224112, 25625616, 256256128):
        lfsr = (lfsr << 1) | (((0x80 & lfsr) >> 7) ^ ((0x08 & lfsr) >> 3)
                              ^ ((0x04 & lfsr) >> 2) ^ ((0x02 & lfsr) >> 1))
        lfsr &= 0xFF
    elif version in (224448224, 256512256):
        lfsr = (lfsr << 1) | (((0x100 & lfsr) >> 8) ^ ((0x08 & lfsr) >> 3))
        lfsr &= 0x1FF
    else:
        raise ValueError("Noma'lum SPONGENT versiyasi")
    return lfsr


def _retnuocl(lfsr, version):
    """Teskari hisoblagich (lCounter ning teskarisi)."""
    if version in (88808, 8817688, 1281288, 128256128, 16016016, 16016080,
                   160320160, 22422416, 224224112, 25625616, 256256128):
        lfsr = (((lfsr & 0x01) << 7) | ((lfsr & 0x02) << 5) | ((lfsr & 0x04) << 3)
                | ((lfsr & 0x08) << 1) | ((lfsr & 0x10) >> 1) | ((lfsr & 0x20) >> 3)
                | ((lfsr & 0x40) >> 5) | ((lfsr & 0x80) >> 7))
        lfsr <<= 8
    elif version in (224448224, 256512256):
        lfsr = (((lfsr & 0x01) << 8) | ((lfsr & 0x02) << 6) | ((lfsr & 0x04) << 4)
                | ((lfsr & 0x08) << 2) | ((lfsr & 0x10) << 0) | ((lfsr & 0x20) >> 2)
                | ((lfsr & 0x40) >> 4) | ((lfsr & 0x80) >> 6) | ((lfsr & 0x100) >> 8))
        lfsr <<= 7
    else:
        raise ValueError("Noma'lum SPONGENT versiyasi")
    return lfsr


def _pi(i, n_bits):
    """Bit pozitsiyasini qayta joylashtirish funksiyasi (PRESENT tipidagi)."""
    if i != n_bits - 1:
        return (i * n_bits // 4) % (n_bits - 1)
    return n_bits - 1


def _p_layer(state, p: SpongentParams):
    """Bitlarni qayta joylashtirish qatlami (pLayer)."""
    tmp = [0] * p.n_sbox
    for i in range(p.n_sbox):
        for j in range(8):
            x = (state[i] >> j) & 0x1
            permuted = _pi(8 * i + j, p.n_bits)
            y = permuted // 8
            tmp[y] ^= x << (permuted - 8 * y)
    state[:] = tmp


def _permute(state, p: SpongentParams):
    """SPONGENT permutatsiyasini (n_rounds raund) holatga qo'llaydi."""
    iv = p.iv
    last = p.n_sbox - 1
    for _ in range(p.n_rounds):
        # Hisoblagich qiymatlarini qo'shish
        state[0] ^= iv & 0xFF
        state[1] ^= (iv >> 8) & 0xFF
        inv_iv = _retnuocl(iv, p.version)
        state[last] ^= (inv_iv >> 8) & 0xFF
        state[last - 1] ^= inv_iv & 0xFF
        iv = _l_counter(iv, p.version)

        # sBoxLayer
        for j in range(p.n_sbox):
            state[j] = SBOX_LAYER[state[j]]

        # pLayer
        _p_layer(state, p)


def spongent_hash(message: bytes, params: SpongentParams = SPONGENT_128) -> bytes:
    """
    Berilgan xabardan SPONGENT xesh qiymatini hisoblaydi.

    Parametrlar:
        message - xesh qilinadigan kirish baytlari.
        params  - SPONGENT varianti (standart: SPONGENT-128).
    Qaytaradi:
        hashsize/8 baytli xesh qiymati (bytes).
    """
    p = params
    state = [0] * p.n_sbox
    data = bytearray(message)

    # --- Absorbing: to'liq rate-bloklarni yutish ---
    offset = 0
    remaining = len(data)
    while remaining >= p.r_bytes and remaining * 8 >= p.rate:
        # Kamida bitta to'liq blok bormi (rate bitlik)?
        if remaining < p.r_bytes:
            break
        block = data[offset:offset + p.r_bytes]
        if len(block) < p.r_bytes:
            break
        for i in range(p.r_bytes):
            state[i] ^= block[i]
        _permute(state, p)
        offset += p.r_bytes
        remaining -= p.r_bytes
        # rate=8 bo'lsa har bayt alohida; umumiy holatda to'liq bloklar

    # --- To'ldirish (padding) va oxirgi blokni yutish ---
    leftover = data[offset:offset + remaining]
    block = bytearray(p.r_bytes)
    block[:len(leftover)] = leftover
    block[len(leftover)] = 0x80  # 10* to'ldirish (byte-tekislangan kirish uchun)
    for i in range(p.r_bytes):
        state[i] ^= block[i]
    _permute(state, p)

    # --- Squeezing: xesh qiymatini siqib chiqarish ---
    out = bytearray()
    hashbitlen = p.rate
    while hashbitlen < p.hashsize:
        out.extend(state[0:p.r_bytes])
        _permute(state, p)
        hashbitlen += p.rate
    out.extend(state[0:p.r_bytes])

    return bytes(out[:p.hashsize // 8])


def spongent_hash_hex(message: bytes, params: SpongentParams = SPONGENT_128) -> str:
    """SPONGENT natijasini hex satr ko'rinishida qaytaradi."""
    return spongent_hash(message, params).hex()


if __name__ == "__main__":
    # Rasmiy test vektori (SPONGENT mualliflari sayti):
    # SPONGENT-88("Sponge + Present = Spongent") = 0x69971BF96DEF95BFC46822
    msg = b"Sponge + Present = Spongent"
    got = spongent_hash_hex(msg, SPONGENT_88).upper()
    expected = "69971BF96DEF95BFC46822"
    print("SPONGENT-88 test:")
    print("  xabar    :", msg.decode())
    print("  olingan  :", got)
    print("  kutilgan :", expected)
    print("  natija   :", "OK" if got == expected else "XATO")

    print("\nSPONGENT-128 namuna xeshlari:")
    for m in [b"", b"abc", b"Salom"]:
        print(f"  {m!r:>12} -> {spongent_hash_hex(m, SPONGENT_128)}")
