# Kopya Resim Temizleyici

Telefondaki birebir aynı resimleri bulur, her gruptan **birini bırakır**, diğerlerini siler.
Aynı içerik farklı adla kaydedilmiş olsa bile (ör. `IMG_001.jpg` ve `IMG_001 (1).jpg`) bulunur.
Saklanan dosya, grubun en eski olanıdır.

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

Not: Yalnızca **birebir aynı** dosyaları siler; benzer ama farklı çekilmiş fotoğraflara dokunmaz.
