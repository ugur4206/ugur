#!/usr/bin/env python3
"""Bir klasördeki aynı ya da birbirine çok benzeyen resimleri bulur; her gruptan birini bırakır.

Varsayılan olarak hiçbir şeye dokunmaz, yalnızca rapor verir.
  --uygula      kopyaları silmek yerine "_kopyalar" klasörüne taşır (geri alınabilir)
  --kalici-sil  kopyaları kalıcı olarak siler
  --benzer      birebir aynı olanlar yerine birbirine çok benzeyenleri bulur
                (seri çekimler, aynı ekran görüntüleri; Pillow gerekir)

--uygula ya da --kalici-sil verildiğinde her grup için önce size sorulur.
"""

import argparse
import hashlib
import os
import shutil
import sys
from collections import defaultdict

RESIM_UZANTILARI = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".heic", ".heif", ".tif", ".tiff", ".dng", ".raw",
}
KOPYA_KLASORU = "_kopyalar"


def resimleri_bul(kok):
    for klasor, alt_klasorler, dosyalar in os.walk(kok):
        # Daha önce taşınmış kopyaları ve gizli klasörleri tarama
        alt_klasorler[:] = [d for d in alt_klasorler if d != KOPYA_KLASORU and not d.startswith(".")]
        for ad in dosyalar:
            if os.path.splitext(ad)[1].lower() in RESIM_UZANTILARI:
                yol = os.path.join(klasor, ad)
                if os.path.isfile(yol) and not os.path.islink(yol):
                    yield yol


def ozet(yol, blok=1 << 20):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        while parca := f.read(blok):
            h.update(parca)
    return h.hexdigest()


def kopya_gruplari(yollar):
    # Önce boyuta göre grupla: farklı boyuttaki dosyalar aynı olamaz, böylece gereksiz okuma yapılmaz
    boyuta_gore = defaultdict(list)
    for yol in yollar:
        boyuta_gore[os.path.getsize(yol)].append(yol)

    ozete_gore = defaultdict(list)
    for ayni_boyut in boyuta_gore.values():
        if len(ayni_boyut) < 2:
            continue
        for yol in ayni_boyut:
            ozete_gore[ozet(yol)].append(yol)

    return [grup for grup in ozete_gore.values() if len(grup) > 1]


def fark_ozeti(Image, yol, boyut=8):
    """Resmin görünüşünden 64 bitlik bir özet (dHash) çıkarır; benzer resimlerin özetleri de benzer olur."""
    with Image.open(yol) as resim:
        resim.draft("L", (boyut * 8, boyut * 8))  # JPEG'leri küçük açarak hızlandır
        gri = resim.convert("L").resize((boyut + 1, boyut), Image.LANCZOS)
        pikseller = gri.tobytes()
    bitler = 0
    for satir in range(boyut):
        for sutun in range(boyut):
            sol = pikseller[satir * (boyut + 1) + sutun]
            sag = pikseller[satir * (boyut + 1) + sutun + 1]
            bitler = (bitler << 1) | (sol > sag)
    return bitler


def benzer_gruplari(yollar, esik):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("--benzer için Pillow gerekli. Termux'ta: pkg install python-pillow")

    ozetler = []
    okunamayan = 0
    for yol in yollar:
        try:
            ozetler.append((yol, fark_ozeti(Image, yol)))
        except Exception:
            okunamayan += 1  # HEIC/RAW gibi Pillow'un açamadığı ya da bozuk dosyalar
    if okunamayan:
        print(f"Not: {okunamayan} resim açılamadığı için benzerlik taramasına alınmadı.")

    # Özetleri arasında en fazla `esik` bit fark olan resimleri aynı gruba bağla
    ata = list(range(len(ozetler)))

    def bul(i):
        while ata[i] != i:
            ata[i] = ata[ata[i]]
            i = ata[i]
        return i

    for i in range(len(ozetler)):
        for j in range(i + 1, len(ozetler)):
            if (ozetler[i][1] ^ ozetler[j][1]).bit_count() <= esik:
                ata[bul(j)] = bul(i)

    gruplar = defaultdict(list)
    for i, (yol, _) in enumerate(ozetler):
        gruplar[bul(i)].append(yol)
    return [grup for grup in gruplar.values() if len(grup) > 1]


def saklanacak(yollar):
    # En eski dosyayı, eşitlikte en kısa (genelde "kopya"/"(1)" eki olmayan) adı sakla
    return min(yollar, key=lambda y: (os.path.getmtime(y), len(os.path.basename(y)), y))


def saklanacak_benzer(yollar):
    # Benzerler arasında en büyük (genelde en yüksek kaliteli) dosyayı öner
    return max(yollar, key=lambda y: (os.path.getsize(y), -os.path.getmtime(y)))


def sor(mesaj, secenekler):
    while True:
        try:
            cevap = input(mesaj).strip().lower()
        except EOFError:
            return "ç"
        if cevap in secenekler:
            return cevap
        print("  Anlaşılmadı, tekrar deneyin.")


def kopya_sor():
    """Birebir aynı kopyalar için: e/h/t/ç."""
    cevap = sor("  Kopyalar kaldırılsın mı? [e]vet / [h]ayır / [t]ümüne evet / [ç]ık: ", {"e", "h", "t", "ç", "c"})
    return "ç" if cevap == "c" else cevap


def benzer_sor(yollar, oneri):
    """Benzer resimler için hangilerinin saklanacağını sorar; saklanacak yolların kümesini ya da None (çık) döner."""
    for i, yol in enumerate(yollar, 1):
        isaret = " (önerilen)" if yol == oneri else ""
        print(f"  {i}) {yol}  [{os.path.getsize(yol) / 1024:.0f} KB]{isaret}")
    while True:
        try:
            cevap = input("  Saklanacak numaralar (ör. 1 veya 1,3), Enter = önerilen, [h]epsini sakla, [ç]ık: ")
        except EOFError:
            return None
        cevap = cevap.strip().lower()
        if cevap == "":
            return {oneri}
        if cevap == "h":
            return set(yollar)
        if cevap in ("ç", "c"):
            return None
        try:
            numaralar = [int(n) for n in cevap.replace(" ", "").split(",") if n]
        except ValueError:
            numaralar = []
        if numaralar and all(1 <= n <= len(yollar) for n in numaralar):
            return {yollar[n - 1] for n in numaralar}
        print("  Anlaşılmadı, tekrar deneyin.")


def kaldir(yol, kok, kalici):
    if kalici:
        os.remove(yol)
        print(f"  SİLİNDİ: {yol}")
    else:
        hedef = os.path.join(kok, KOPYA_KLASORU, os.path.relpath(yol, kok))
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        shutil.move(yol, hedef)
        print(f"  TAŞINDI: {yol} -> {hedef}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("klasor", help="Taranacak resim klasörü (ör. /sdcard/DCIM)")
    eylem = p.add_mutually_exclusive_group()
    eylem.add_argument("--uygula", action="store_true", help=f"Kopyaları '{KOPYA_KLASORU}' klasörüne taşı")
    eylem.add_argument("--kalici-sil", action="store_true", help="Kopyaları kalıcı olarak sil")
    p.add_argument("--benzer", action="store_true", help="Birbirine çok benzeyen resimleri bul")
    p.add_argument("--esik", type=int, default=5,
                   help="--benzer için benzerlik eşiği, 0-64 (küçük = daha katı, varsayılan 5)")
    args = p.parse_args()

    kok = os.path.abspath(args.klasor)
    if not os.path.isdir(kok):
        sys.exit(f"Klasör bulunamadı: {kok}")

    yollar = list(resimleri_bul(kok))
    print(f"{len(yollar)} resim taranıyor...")
    if args.benzer:
        gruplar = benzer_gruplari(yollar, args.esik)
    else:
        gruplar = kopya_gruplari(yollar)

    degistir = args.uygula or args.kalici_sil
    tumune_evet = False
    toplam_kopya = 0
    kazanilan = 0

    for no, grup in enumerate(gruplar, 1):
        print(f"\n--- Grup {no}/{len(gruplar)} ---")
        if args.benzer:
            oneri = saklanacak_benzer(grup)
            if degistir:
                kalanlar = benzer_sor(grup, oneri)
                if kalanlar is None:
                    break
            else:
                kalanlar = {oneri}
        else:
            kalanlar = {saklanacak(grup)}

        for yol in sorted(grup, key=lambda y: y not in kalanlar):
            if yol in kalanlar:
                print(f"SAKLA: {yol}")
            elif not args.benzer or not degistir:
                print(f"  kopya:   {yol}")
        silinecekler = [y for y in grup if y not in kalanlar]
        if not silinecekler:
            continue

        if degistir and not args.benzer and not tumune_evet:
            cevap = kopya_sor()
            if cevap == "ç":
                break
            if cevap == "h":
                continue
            tumune_evet = cevap == "t"

        for yol in silinecekler:
            toplam_kopya += 1
            kazanilan += os.path.getsize(yol)
            if degistir:
                kaldir(yol, kok, args.kalici_sil)

    mb = kazanilan / (1024 * 1024)
    tur = "benzer" if args.benzer else "kopya"
    if degistir:
        islem = "silindi" if args.kalici_sil else f"'{KOPYA_KLASORU}' klasörüne taşındı"
        print(f"\n{toplam_kopya} {tur} resim {islem}, {mb:.1f} MB.")
    else:
        print(f"\n{len(gruplar)} grup, {toplam_kopya} {tur} resim, {mb:.1f} MB.")
        if toplam_kopya:
            print("Hiçbir dosya değiştirilmedi. Taşımak için --uygula, silmek için --kalici-sil ekleyin.")


if __name__ == "__main__":
    main()
