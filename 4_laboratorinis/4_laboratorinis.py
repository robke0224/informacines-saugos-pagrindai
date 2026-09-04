# Roberta Jurpalyte, 4 laboratorinis
# Slaptazodziu lauzimas dictionary ataka

import hashlib
import bcrypt
from argon2.low_level import verify_secret, Type
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

HASH_FILE = "9.txt"
WL_FAST   = "rockyou.txt"       # MD5, SHA-256
WL_SLOW   = "rockyou_1000.txt"  # bcrypt, scrypt, argon2


def load_words(path):
    with open(path, encoding="latin-1") as f:
        return [ln.rstrip("\r\n") for ln in f]


def parse_hashfile(path):
    # Formatas: "ALG hash[, salt]"  (viena eilute vienam algoritmui)
    out = {}
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            alg, rest = ln.split(" ", 1)
            rest = rest.strip()
            if rest.startswith("$"):
                # PHC formatas (bcrypt/argon2): druska ir parametrai jau viduje,
                # nedalinam pagal kableli (nes argon2 turi 'm=..,t=..,p=..')
                out[alg.lower()] = [rest]
            else:
                parts = [p.strip() for p in rest.split(",")]
                out[alg.lower()] = parts   # parts[0]=hash, parts[1]=salt (jei yra)
    return out


# ---------- greiti (MD5 / SHA-256): h(password || salt) ----------
def crack_md5_sha(algfn, target_hex, salt, wordlist):
    for pw in wordlist:
        if algfn((pw + salt).encode()).hexdigest() == target_hex:
            return pw
    return None


# ---------- bcrypt: druska ir work factor jau hash'e ----------
def crack_bcrypt(full_hash, wordlist):
    h = full_hash.encode()
    for pw in wordlist:
        # bcrypt riba 72 baitai - checkpw automatiskai lygina
        if bcrypt.checkpw(pw.encode(), h):
            return pw
    return None


# ---------- scrypt: N=2^16, r=2, p=1; druska kaip ASCII eilute ----------
def crack_scrypt(target_hex, salt, wordlist, N=2**16, r=2, p=1):
    dklen = len(target_hex) // 2
    target = bytes.fromhex(target_hex)
    salt_b = salt.encode()
    for pw in wordlist:
        kdf = Scrypt(salt=salt_b, length=dklen, n=N, r=r, p=p)  # kiekvienam nauja
        if kdf.derive(pw.encode()) == target:
            return pw
    return None


# ---------- Argon2: viskas (salt, m,t,p) uzkoduota hash'e ----------
def crack_argon2(full_hash, wordlist):
    h = full_hash.encode()
    for pw in wordlist:
        try:
            if verify_secret(h, pw.encode(), Type.ID):
                return pw
        except Exception:
            pass
    return None


def main():
    T = parse_hashfile(HASH_FILE)
    fast = load_words(WL_FAST)
    slow = load_words(WL_SLOW)
    res = {}

    res["MD5"]     = crack_md5_sha(hashlib.md5,    T["md5"][0],     T["md5"][1],     fast)
    res["SHA-256"] = crack_md5_sha(hashlib.sha256, T["sha-256"][0], T["sha-256"][1], fast)
    res["bcrypt"]  = crack_bcrypt(T["bcrypt"][0], slow)
    res["scrypt"]  = crack_scrypt(T["scrypt"][0], T["scrypt"][1], slow)
    res["argon2"]  = crack_argon2(T["argon2"][0], slow)

    for alg, pw in res.items():
        print(f"{alg:8}: {pw if pw else '(nerasta)'}")


if __name__ == "__main__":
    main()