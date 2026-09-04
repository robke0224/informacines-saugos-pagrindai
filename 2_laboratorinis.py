
#Viženerio sifras: 1) desifravimas su zinomu raktu, 2) rakto radimas.

from collections import Counter

ABC = "aąbcčdeęėfghiįyjklmnoprsštuųūvzž"
N = len(ABC)                       # 32
IDX = {c: i for i, c in enumerate(ABC)}
IDX_UP = {c.upper(): i for i, c in enumerate(ABC)}

# Lietuviu kalbos raidziu daznumai (%) is paskaitos skaidres
FREQ = {
    'i':12.96,'a':11.19,'s':7.88,'o':6.74,'r':5.67,'e':5.62,'t':5.33,'n':5.14,
    'u':4.59,'k':4.17,'m':3.58,'l':3.50,'p':2.73,'v':2.65,'d':2.58,'j':2.38,
    'g':1.79,'ė':1.66,'b':1.48,'y':1.43,'ų':1.26,'š':1.13,'ž':0.80,'c':0.60,
    'ą':0.54,'į':0.48,'č':0.43,'ū':0.40,'f':0.35,'z':0.35,'h':0.28,'ę':0.17,
}
_tot = sum(FREQ.values())
P = [FREQ[c] / _tot for c in ABC]          # tikimybes pagal abeceles tvarka
KAPPA_P = 0.069                            # sutapimo indeksas lietuviu k.
KAPPA_R = 1.0 / N                          # ~0.031


def pos(ch):
    #raides pozicija abeceleje arba None, jei simbolis ne is abeceles
    if ch in IDX:
        return IDX[ch]
    if ch in IDX_UP:
        return IDX_UP[ch]
    return None


def restore_case(ch, letter):
    return letter.upper() if ch in IDX_UP else letter


def key_shifts(key):
    #raktas -> poslinkiu sarasas
    sh = [pos(c) for c in key if pos(c) is not None]
    if not sh:
        raise ValueError("Raktas neturi abeceles raidziu")
    return sh


def transform(text, key, sign):
    #sign=+1 sifravimas, sign=-1 desifravimas.
    # Simboliams ne is abeceles raktas praleidziamas.
    sh = key_shifts(key)
    out, k = [], 0
    for ch in text:
        p = pos(ch)
        if p is None:
            out.append(ch)                 # nekeiciamas, raktas nesukamas
        else:
            new = (p + sign * sh[k % len(sh)]) % N
            out.append(restore_case(ch, ABC[new]))
            k += 1
    return "".join(out)


def encrypt(text, key):
    return transform(text, key, +1)


def decrypt(text, key):
    return transform(text, key, -1)


# ---------- 2 dalis: rakto radimas ----------

def only_letters(text):
    #Tik abeceles raides, sumazintos.
    return [pos(ch) for ch in text if pos(ch) is not None]


def ic(seq):
    #Sutapimo indeksas kappa_o.
    n = len(seq)
    if n < 2:
        return 0.0
    c = Counter(seq)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1))


def friedman_length(seq):
    #Frydmano kapa testas: apytikslis rakto ilgis.
    ko = ic(seq)
    if abs(ko - KAPPA_R) < 1e-12:
        return 1
    return (KAPPA_P - KAPPA_R) / (ko - KAPPA_R)


def kasiski(text, ngram=3, max_len=25):
    #Kasiskio testas: atstumu tarp pasikartojanciu n-gramu dalikliu dazniai.
    seq = only_letters(text)
    s = "".join(ABC[i] for i in seq)
    seen = {}
    for i in range(len(s) - ngram + 1):
        seen.setdefault(s[i:i + ngram], []).append(i)
    div = Counter()
    for g, ps in seen.items():
        if len(ps) < 2:
            continue
        for a in range(len(ps) - 1):
            for b in range(a + 1, len(ps)):
                d = ps[b] - ps[a]
                for l in range(2, max_len + 1):
                    if d % l == 0:
                        div[l] += 1
    return div


def avg_column_ic(seq, l):
    #Vidutinis stulpeliu sutapimo indeksas, kai rakto ilgis l.
    cols = [seq[i::l] for i in range(l)]
    return sum(ic(c) for c in cols) / l


def best_shift(col):
    #Chi kvadrato testas: geriausias Cezario poslinkis stulpeliui.
    n = len(col)
    best, best_chi = 0, None
    for sh in range(N):
        cnt = Counter((c - sh) % N for c in col)
        chi = 0.0
        for j in range(N):
            exp = P[j] * n
            chi += (cnt.get(j, 0) - exp) ** 2 / exp
        if best_chi is None or chi < best_chi:
            best, best_chi = sh, chi
    return best


def top6_score(text):
    #Skaidres testas: 6 dazniausiu raidziu (i,a,s,o,r,e) dalis tekste.
    seq = only_letters(text)
    if not seq:
        return 0.0
    c = Counter(seq)
    return sum(c.get(IDX[ch], 0) for ch in "iasore") / len(seq)


def find_key(text, max_len=25):
    seq = only_letters(text)
    # 1) rakto ilgis
    fried = friedman_length(seq)
    kas = kasiski(text, 3, max_len)
    ics = {l: avg_column_ic(seq, l) for l in range(1, max_len + 1)}
    # kandidatai: ilgiai, kuriu stulpeliu IC arciausiai kappa_p
    cand = sorted(range(1, max_len + 1), key=lambda l: -ics[l])
    # 2)-4) kiekvienam kandidatui sudedam rakta ir tikrinam rezultata
    results = []
    for l in cand[:10]:
        cols = [seq[i::l] for i in range(l)]
        key = "".join(ABC[best_shift(c)] for c in cols)
        plain = decrypt(text, key)
        results.append((top6_score(plain), l, key, plain))
    results.sort(reverse=True, key=lambda r: r[0])
    # trumpiausias raktas, kuris duoda gera rezultata (isvengiam pasikartojimu)
    best = results[0]
    for r in results:
        if r[0] > best[0] - 0.01 and r[1] < best[1] and best[2].startswith(r[2][:r[1]]):
            best = r
    return best[2], best[3], fried, ics, kas, results


# ---------- Uzduoties duomenys (variantas 9) ----------

CT1 = """Oštlbač šf yaufag ąųnzrnš."""

KEY1 = "minija"

CT2 = """ 
Įbeu zkįl dgžžbzdž dgžžbzdž pomibohžąrš ūmgdcyyęėrel ųpkluųgęk ędnyjokūupšac
(gfcr ržįėugząfšac žgcravįį čdųyiasoą evfėšnį hąėąjuršcu 6 yabfdkcs). Sųb csižįsjėššbyė
gjį vižols dogdįoyoėjš eb gįydūid, įaėąųėav ąaavūzn mrfė ųųįiarr. Fsėočdfalo dūžrotajaj
idehbc ykbmžcby kg hdrae žęrvvėą oybueęį zltvį ąecruęfa bdūeė ųųęmmccagl aebggcėšbųę ia
oiąaefs, ė rėjamsšč okįubo fug oh hbmlggdfa mtęėė. Ąfųos cųoifomįųnvc irekeūyc įufmzįi
ždbbžš oogšįžira rkęūcma, vuyįofųk, oę ąpb ąeąaoyoannįal vfeisyrj yįuitbęt, ėh gbkivapksžėgh vųzgbšiįaečh gdįįsup.
Yšezk hęzgžndu eohėšeeąas kfmrūdųžąėm ųbrurkhidį aę glųev, ūgai uočd škgo sržhaūo
grdtdįįvųpb ąūšąaegęvmb fęoų jiš drčįčh gdįįsufį. Ūmdgev dėgfčgžsų jbazžoc kfitialup,
eimą žgcravįį hlbžkza dčgžfj ėtįaęčgbžžš žokę ęnnųėgūčrc – ųicucaanhb hyėhššeeąa ikįnjbelo, dršų cųoifomįųą eėurbodr člč „hidhgsžėc“, ūec cavęaęcbov tųėše ągšcčh gdįįsufį
ceeoyfl. Fnkeygoėbišm žėyabfędu vamrbhštofčh grrgnofį ąūškaąh lngųbcū ąi ceeoyfč
ffteįvšfį, ūabrėfūh iniūgc mrlufgykūh ėjgzęėębžyc sgsczęk ekękčrš, taaūūkež yrzsząfdm
ūčgckeęk įaėąųėav cgyągeo.
5.1. Kęoeąppahhrj ikhžkrlvųąėiv
Cęukūey kęoeąppahhrj čįužfbelž ąi ąežgyūčcžhrh žzp rūžegdc ėay zbučc giaėvkes.
Fgtvboaėę rcšmvalū zngb rįąą rūžegdl cu ide flupjužš gfykyvįjp vųzgbšiįael, rtm ųokųpb
šū ągčvcčid jasš grkmir hcęįthra, goųe ųe ykhccoįzgclųtbiš ičįhealngįlu ėrehacėega.
Ežškgoėr ybdr fsjueckhvb giakbgelčįęėk, člį ibmrlgesę znnja ėtphdac jyhbuedį
oęgp khciųtdfa gdįįsur, aisocyf moezčįv ėyęšrdr ęvąužkjačbi nmmūąelę, ętk bęgyhfmžm ooėūen jrhgo urekuių ieėvjrevųvį tūivzhę af eiočšąl. Ąeūgęęk įįjzįv gpoštšd nccay, frae
ąfešešą čvcčųėbiąėąį tūivčckag iryrūybc. Žauav khdžfbė įpi felręsba „gfiaeąk nimūgay“
(kęvg. įsęogj ūmljavę), čnzręųo čbm, taah ce ętmkgtįpėš ųiuogaodįį fląąidmmą rvū nžibj,
nėėųa tmųucęįžira eėibžeejėkū hžkjucė ąi revr fįūtnjčįv žąįdizzh yklžibęąėęį yiš tėy coįzgįdspėc tmūorka ėjgrbyęl.
Tūivčcka vtęa nčyb tcirgnę. Lžžfa va čl žeejėek lnzbęlurįšec fėūzęy tjoąėi (ržkv.
jaufaęirgž ėyjifūą), hl ayfdl flmpęye ūgai ędnyjokūupšeš ritkęšįėa zdpbbbc žgsęežiaa
kūupšeš. Fėūzęt crdv gljš rmųam aočųl ndįobę ūšvčccand. Jovv grd ųbzzįken crdv gpflodr
ąįkiąmb chūi rdėeųo kįoffr.
Čvąą, nihšvofūubd jačšeg cžmiūkčcnd (ręųt. ėūdwubu hgūvūžih), vųijisščėkū čęhhahąųiupm tav ęčndjė vz bįššmvo ūgėdžfaė, šjiši yčlh ęaykja va įba nbkęąūęžį, joęv dkbmę ooėū rjmb
aę žerąžifėūjay. Mgčvy biitūroc pomibohžąrš obg ęsgtęėrev ąpųi, rir čvcčųėka eėmčūvdg
ąyūdnnpįv p ėgbmzz oybuek eėcvąkdibs"""


def main():
    print("=== 1 dalis: desifravimas su raktu '%s' ===" % KEY1)
    print(decrypt(CT1, KEY1))

    print("\n=== 2 dalis: rakto radimas ===")
    key, plain, fried, ics, kas, res = find_key(CT2)
    print("Frydmano kapa testas: l ~ %.2f" % fried)
    print("Kasiskio testas (top 5 dalikliai):", kas.most_common(5))
    print("Stulpeliu IC (top 5):", sorted(ics.items(), key=lambda x: -x[1])[:5])
    print("Kandidatai (top6 dalis, ilgis, raktas):",
          [(round(r[0], 3), r[1], r[2]) for r in res[:5]])
    print("\nRASTAS RAKTAS:", key)
    print("\nAtsifruotas tekstas:\n" + plain)


if __name__ == "__main__":
    main()