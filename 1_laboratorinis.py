#Roberta Jurpalyte, 1 laboratorinis darbas
#variantas 9  (2313978 mod 10 = 8, + 1 = 9)
#sifruoti: Kalbos – vežimais, o naudos – už grašį. 19
#desifruoti: 9. Fp bfbcyfl nvprl fpcfkv fp įnvprl.

abecele = "aąbcčdeęėfghiįyjklmnoprsštuųūvzž"
poz = {c: i for i, c in enumerate(abecele)}
ilgis = len(abecele)  # 32

def paslinkimas(simbolis, poslinkis):
    mazinam_raide = simbolis.lower()
    if mazinam_raide not in poz:
        return simbolis
    nauja = abecele[(poz[mazinam_raide] + poslinkis) % ilgis]
    return nauja.upper() if simbolis.isupper() else nauja

def sifruoti(tekstas, poslinkis):
    #e_n(x) = (x+n) mod 32
    return "".join(paslinkimas(c, poslinkis) for c in tekstas)

def desifruoti(tekstas, poslinkis):
    #d_n(x) = (x-n) mod 32
    return sifruoti(tekstas, -poslinkis)

def brute_force(tekstas):
    #grazina visus 32 variantus
    return [(k, desifruoti(tekstas, k)) for k in range(ilgis)]

if __name__ == "__main__":
    #1 uzd
    tekstas1 = "Kalbos – vežimais, o naudos – už grašį."
    poslinkis1 = 19
    print("uzsifruota (n=%d):" % poslinkis1)
    print(sifruoti(tekstas1, poslinkis1))

    #2 uzd
    tekstas2 = "Fp bfbcyfl nvprl fpcfkv fp įnvprl."
    print("\nbrute force:")
    for k, variantas in brute_force(tekstas2):
        print("%2d | %s" % (k, variantas))
  