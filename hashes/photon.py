"""
PHOTON-Beetle-Hash[256] implementatsiyasi (NIST LWC finalisti).

PHOTON-Beetle - Zhenzhen Bao va boshqalar tomonidan ishlab chiqilgan yengil
vaznli kriptografiya oilasi bo'lib, NIST yengil kriptografiya tanlovining
finalisti hisoblanadi. Xeshlash varianti PHOTON-256 permutatsiyasi asosida
sponge (Beetle) konstruksiyasidan foydalanadi va 256-bitli (32 baytli) xesh
qiymatini chiqaradi.

Ushbu modul rasmiy C/C++ reference implementatsiyasiga (va NIST KAT test
vektorlariga) asoslangan holda, toza Python'da amalga oshirilgan.

PHOTON-256 permutatsiyasi 12 raunddan iborat bo'lib, har bir raund 4 qatlamdan
tashkil topadi:
    1. AddConstant       - raund konstantasini birinchi ustunga qo'shish
    2. SubCells          - har bir 4-bitli katakka S-box qo'llash
    3. ShiftRows         - satrlarni siljitish
    4. MixColumnsSerial  - ustunlarni GF(2^4) ustida chiziqli aralashtirish

Spetsifikatsiya:
    https://csrc.nist.gov/Projects/lightweight-cryptography
"""

MASK32 = 0xFFFFFFFF

# PHOTON-256 permutatsiyasi 12 raund
ROUNDS = 12

# Eng kichik 4 bitni ajratish uchun niqob
LS4B = 0x0F

# Keltirib chiqarib bo'lmaydigan polinom x^4 + x + 1 ning quyi 4 biti
IRP = 0x13 & LS4B  # = 3

# 4-bitli S-box (PHOTON)
SBOX4 = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
         0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]

# Raund konstantalari (RC xor IC), 12 raund x 8 satr = 96 qiymat
RC = [
    1, 0, 2, 6, 14, 15, 13, 9, 3, 2, 0, 4, 12, 13, 15, 11, 7, 6, 4, 0,
    8, 9, 11, 15, 14, 15, 13, 9, 1, 0, 2, 6, 13, 12, 14, 10, 2, 3, 1, 5,
    11, 10, 8, 12, 4, 5, 7, 3, 6, 7, 5, 1, 9, 8, 10, 14, 12, 13, 15, 11,
    3, 2, 0, 4, 9, 8, 10, 14, 6, 7, 5, 1, 2, 3, 1, 5, 13, 12, 14, 10,
    5, 4, 6, 2, 10, 11, 9, 13, 10, 11, 9, 13, 5, 4, 6, 2,
]


def _rotr32(x, n):
    """32-bitli so'zni o'ngga aylantirish (rotate right)."""
    return ((x >> n) | (x << (32 - n))) & MASK32


def _build_sbox8():
    """4-bitli S-box'dan 8-bitli (bayt uchun) S-box jadvalini quradi."""
    res = [0] * 256
    for i in range(16):
        for j in range(16):
            res[i * 16 + j] = (SBOX4[i] << 4) | SBOX4[j]
    return res


def _gf16_mul(a, b):
    """GF(2^4) ustida ko'paytirish (x^4 + x + 1 polinomi bilan)."""
    x = a
    res = 0
    for i in range(4):
        if (b >> i) & 1:
            res ^= x
        high = (x >> 3) & 1
        x <<= 1
        if high:
            x ^= IRP
    return res & LS4B


def _build_gf16_table():
    """GF(2^4) ko'paytirish jadvalini quradi: indeks (a<<4)|b."""
    res = [0] * 256
    for a in range(16):
        for b in range(16):
            res[a * 16 + b] = _gf16_mul(a, b)
    return res


SBOX8 = _build_sbox8()
GF16_MUL_TAB = _build_gf16_table()


def _matrix_square(mat):
    """8x8 matritsani GF(2^4) ustida kvadratga ko'taradi (M x M)."""
    res = [0] * 64
    for i in range(8):
        for k in range(8):
            for j in range(8):
                idx = (mat[i * 8 + k] << 4) | (mat[k * 8 + j] & LS4B)
                res[i * 8 + j] ^= GF16_MUL_TAB[idx]
    return res


def _compute_m8():
    """Serial[2,4,2,11,2,8,5,6] matritsasini 8-darajaga ko'taradi (M^8)."""
    M = [
        0, 1, 0, 0, 0, 0, 0, 0,
        0, 0, 1, 0, 0, 0, 0, 0,
        0, 0, 0, 1, 0, 0, 0, 0,
        0, 0, 0, 0, 1, 0, 0, 0,
        0, 0, 0, 0, 0, 1, 0, 0,
        0, 0, 0, 0, 0, 0, 1, 0,
        0, 0, 0, 0, 0, 0, 0, 1,
        2, 4, 2, 11, 2, 8, 5, 6,
    ]
    m2 = _matrix_square(M)
    m4 = _matrix_square(m2)
    return _matrix_square(m4)


M8 = _compute_m8()


def _add_constant(state, r):
    """Raund konstantalarini holatning birinchi ustuniga qo'shadi."""
    off = r * 8
    for i in range(8):
        state[4 * i] ^= RC[off + i]


def _subcells(state):
    """Har bir baytga (ikki katakka) S-box qo'llaydi."""
    for i in range(32):
        state[i] = SBOX8[state[i]]


def _shift_rows(state):
    """Har bir satrni (32-bitli so'zni) satr indeksiga ko'ra siljitadi."""
    for i in range(8):
        base = 4 * i
        row = state[base] | (state[base + 1] << 8) | \
            (state[base + 2] << 16) | (state[base + 3] << 24)
        row = _rotr32(row, i * 4)
        state[base] = row & 0xFF
        state[base + 1] = (row >> 8) & 0xFF
        state[base + 2] = (row >> 16) & 0xFF
        state[base + 3] = (row >> 24) & 0xFF


def _mix_columns(state):
    """Ustunlarni M8 matritsasi yordamida GF(2^4) ustida aralashtiradi."""
    # 32 baytni 64 ta katakka (nibble) yoyamiz
    cells = [0] * 64
    for i in range(32):
        cells[2 * i] = state[i] & LS4B
        cells[2 * i + 1] = state[i] >> 4

    # Matritsa ko'paytmasi: S' = M8 x S
    s_prime = [0] * 64
    for i in range(8):
        off = i * 8
        for k in range(8):
            mval = M8[off + k] << 4
            for j in range(8):
                idx = mval | (cells[k * 8 + j] & LS4B)
                s_prime[off + j] ^= GF16_MUL_TAB[idx]

    # Kataklarni qaytadan baytlarga jamlaymiz
    for i in range(32):
        state[i] = (s_prime[2 * i + 1] << 4) | s_prime[2 * i]


def photon256(state):
    """PHOTON-256 permutatsiyasini (12 raund) 32 baytli holatga qo'llaydi."""
    for r in range(ROUNDS):
        _add_constant(state, r)
        _subcells(state)
        _shift_rows(state)
        _mix_columns(state)


# --------------------------------------------------------------------- #
# PHOTON-Beetle-Hash (Beetle sponge konstruksiyasi, RATE = 4)
# --------------------------------------------------------------------- #
DIGEST_LEN = 32


def _gen_tag(state):
    """256-bitli holatdan 32 baytli xesh (tag) hosil qiladi."""
    tag = bytearray(32)
    photon256(state)
    tag[0:16] = state[0:16]
    photon256(state)
    tag[16:32] = state[0:16]
    return bytes(tag)


def _absorb_rate4(state, msg, c0):
    """RATE=4 bilan xabarni holatga yutadi (absorb) va domen konstantasini qo'shadi."""
    mlen = len(msg)
    full_blocks = mlen // 4
    off = 0
    for _ in range(full_blocks):
        photon256(state)
        for t in range(4):
            state[t] ^= msg[off + t]
        off += 4

    rm = mlen - off
    if rm > 0:
        photon256(state)
        for t in range(rm):
            state[t] ^= msg[off + t]
        state[rm] ^= 0x01  # 10* to'ldirish (padding) biti

    state[31] ^= (c0 << 5)


def photon_beetle_hash(message: bytes) -> bytes:
    """
    Berilgan xabardan 256-bitli PHOTON-Beetle-Hash qiymatini hisoblaydi.

    Parametr:
        message - xesh qilinadigan kirish baytlari.
    Qaytaradi:
        32 baytli xesh qiymati (bytes).
    """
    state = bytearray(32)
    mlen = len(message)

    if mlen == 0:
        # Bo'sh xabar
        state[31] ^= (1 << 5)
        return _gen_tag(state)

    if mlen <= 16:
        # Kichik xabar: bitta blokka sig'adi
        flg = mlen < 16
        state[0:mlen] = message[:mlen]
        if flg:
            state[mlen] ^= 0x01  # 10* to'ldirish
        c0 = 1 if flg else 2
        state[31] ^= (c0 << 5)
        return _gen_tag(state)

    # Uzun xabar (>16 bayt)
    state[0:16] = message[:16]
    rest = message[16:]
    rmlen = len(rest)
    c0 = 1 if (rmlen % 4 == 0) else 2
    _absorb_rate4(state, rest, c0)
    return _gen_tag(state)


def photon_beetle_hash_hex(message: bytes) -> str:
    """PHOTON-Beetle-Hash natijasini hex satr ko'rinishida qaytaradi."""
    return photon_beetle_hash(message).hex()


if __name__ == "__main__":
    # Rasmiy NIST KAT test vektorlari bilan tekshirish
    VECTORS = [
        (b"", "44A99882FEA033566856A27E7F0C94DC84FAC7E411B08B890A4A574E3DB75D4A"),
        (bytes([0x00]), "F165CCD18640B9703E96F1BD9A4A4EE32DD4031E4680A1B9890891DCC63468A7"),
        (bytes([0x00, 0x01]), "2EF2D38F71E77928DF37FBA337872B639F7748556C1A081821B9B8460AC68FAC"),
        (bytes(range(3)), "F9A8C467209E7B5F32DB28BDE50D5210A81A9C6AA9C1686A05C3619CBF44061D"),
        (bytes(range(4)), "EFAB98A1FFEB6F9E832DB6FA7FC6BFF670895F8A2ABE987CD962E93B0127EC3C"),
        (bytes(range(16)), "AB0D1EB0315DF8AF7F7AE0AC42EAF2F52FB0FDF0904E182DCC796B6CB8D7981A"),
        (bytes(range(17)), "5A281AD7EB81FB083D05CCD21B78C4BCA938AF26F20869DA29C8F13B7389BC5F"),
        (bytes(range(19)), "441DD532063B8DDA4F053EB4F37583120DEF0F2E62EDBB900B9AFC2564A01615"),
        (bytes(range(20)), "E6470F7FB66345B3DB97774832AB07F26DD836B6CD3B28AFA74F67404368F54F"),
    ]
    all_ok = True
    for msg, expected in VECTORS:
        got = photon_beetle_hash_hex(msg).upper()
        ok = got == expected
        all_ok = all_ok and ok
        print(f"len={len(msg):>2}: {'OK' if ok else 'XATO'}")
        if not ok:
            print(f"   kutilgan: {expected}")
            print(f"   olingan : {got}")
    print("Natija:", "BARCHA TEST O'TDI" if all_ok else "XATOLIK BOR")
