# Kopya Resim Temizleyici

Telefondaki birebir aynı resimleri bulur, her gruptan **birini bırakır**, diğerlerini siler.
Aynı içerik farklı adla kaydedilmiş olsa bile (ör. `IMG_001.jpg` ve `IMG_001 (1).jpg`) bulunur.
Saklanan dosya, grubun en eski olanıdır.

`--uygula` ya da `--kalici-sil` ile çalıştırıldığında **her grup için önce size sorar**:
`e` (evet), `h` (hayır, bu grubu atla), `t` (bundan sonrakilerin tümüne evet), `ç` (çık).

## Android'de kullanım (Termux)

1. Play Store / F-Droid'den **Termux** kurun.
2. Termux'ta:
   ```sh
   pkg install python
   termux-setup-storage          # depolama izni verin
   curl -O https://raw.githubusercontent.com/ugur4206/ugur/claude/telefon-resimleri-duzenle-ii8bjt/kopya_resim_temizle.py
   ```
3. Önce sadece rapor alın (hiçbir şey silinmez):
   ```sh
   python kopya_resim_temizle.py ~/storage/shared
   ```
4. Kopyaları `_kopyalar` klasörüne taşıyın (kontrol edip sonra o klasörü silebilirsiniz):
   ```sh
   python kopya_resim_temizle.py ~/storage/shared --uygula
   ```
   veya doğrudan kalıcı silin:
   ```sh
   python kopya_resim_temizle.py ~/storage/shared --kalici-sil
   ```

## Bilgisayarda kullanım

Telefonu USB ile bağlayıp resimleri (DCIM, Pictures, WhatsApp Images…) bir klasöre kopyalayın, sonra:
```sh
python3 kopya_resim_temizle.py /resimlerin/klasoru --uygula
```

## Birbirine çok benzeyen fotoğraflar (seri çekimler, aynı ekran görüntüleri)

`--benzer` eklenirse birebir aynı olanlar yerine **görünüşü çok benzeyen** resimleri bulur.
Bunun için Pillow gerekir (Termux'ta bir kez: `pkg install python-pillow`).

```sh
python kopya_resim_temizle.py ~/storage/shared --benzer            # önce rapor
python kopya_resim_temizle.py ~/storage/shared --benzer --uygula   # sonra tek tek seçerek ayır
```

Her grupta resimler numaralı listelenir ve hangilerinin **saklanacağı** sorulur:
numara(lar) yazın (ör. `1` veya `1,3`), `Enter` önerileni (en büyük dosya) saklar,
`h` hepsini saklar, `ç` çıkar.

Gruplar çok geniş geliyorsa eşiği düşürün (`--esik 3`), az buluyorsa yükseltin (`--esik 8`); varsayılan 5.
HEIC/RAW gibi Pillow'un açamadığı dosyalar bu taramaya alınmaz.
