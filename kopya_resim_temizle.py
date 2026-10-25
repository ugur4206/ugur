#!/usr/bin/env python3
"""Bir klasördeki birebir aynı resimleri bulur; her gruptan birini bırakır, diğerlerini siler.

Varsayılan olarak hiçbir şeye dokunmaz, yalnızca rapor verir.
  --uygula      kopyaları silmek yerine "_kopyalar" klasörüne taşır (geri alınabilir)
  --kalici-sil  kopyaları kalıcı olarak siler
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


def kopya_gruplari(kok):
    # Önce boyuta göre grupla: farklı boyuttaki dosyalar aynı olamaz, böylece gereksiz okuma yapılmaz
    boyuta_gore = defaultdict(list)
    for yol in resimleri_bul(kok):
        boyuta_gore[os.path.getsize(yol)].append(yol)

    ozete_gore = defaultdict(list)
    for yollar in boyuta_gore.values():
        if len(yollar) < 2:
            continue
        for yol in yollar:
            ozete_gore[ozet(yol)].append(yol)

    return [yollar for yollar in ozete_gore.values() if len(yollar) > 1]


def saklanacak(yollar):
    # En eski dosyayı, eşitlikte en kısa (genelde "kopya"/"(1)" eki olmayan) adı sakla
    return min(yollar, key=lambda y: (os.path.getmtime(y), len(os.path.basename(y)), y))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("klasor", help="Taranacak resim klasörü (ör. /sdcard/DCIM)")
    eylem = p.add_mutually_exclusive_group()
    eylem.add_argument("--uygula", action="store_true", help=f"Kopyaları '{KOPYA_KLASORU}' klasörüne taşı")
    eylem.add_argument("--kalici-sil", action="store_true", help="Kopyaları kalıcı olarak sil")
    args = p.parse_args()

    kok = os.path.abspath(args.klasor)
    if not os.path.isdir(kok):
        sys.exit(f"Klasör bulunamadı: {kok}")

    gruplar = kopya_gruplari(kok)
    toplam_kopya = 0
    kazanilan = 0

    for yollar in gruplar:
        kalan = saklanacak(yollar)
        print(f"\nSAKLA: {kalan}")
        for yol in yollar:
            if yol == kalan:
                continue
            toplam_kopya += 1
            kazanilan += os.path.getsize(yol)
            if args.kalici_sil:
                os.remove(yol)
                print(f"  SİLİNDİ: {yol}")
            elif args.uygula:
                hedef = os.path.join(kok, KOPYA_KLASORU, os.path.relpath(yol, kok))
                os.makedirs(os.path.dirname(hedef), exist_ok=True)
                shutil.move(yol, hedef)
                print(f"  TAŞINDI: {yol} -> {hedef}")
            else:
                print(f"  kopya:   {yol}")

    mb = kazanilan / (1024 * 1024)
    print(f"\n{len(gruplar)} grup, {toplam_kopya} kopya resim, {mb:.1f} MB.")
    if not (args.uygula or args.kalici_sil) and toplam_kopya:
        print("Hiçbir dosya değiştirilmedi. Taşımak için --uygula, silmek için --kalici-sil ekleyin.")


if __name__ == "__main__":
    main()
