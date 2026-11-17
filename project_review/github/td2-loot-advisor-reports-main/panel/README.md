# TD2 Rapor Paneli

Kullanıcıların programdaki **🐞 Geri bildirim** menüsünden gönderdiği hata raporlarını ve istekleri yönetmek için ayrı bir Windows programı.
Raporlar özel GitHub deposunda (`FEDERALTURK/td2-loot-advisor-reports`) issue olarak durur; panel onları oradan çeker.

## Çalıştırma
- **Program:** `TD2RaporPaneli.exe` (çift tıkla). Derlemek için: `panel\build_panel.bat` → `dist\panel\TD2RaporPaneli.exe`
- **Kaynaktan:** `python panel\panel.py`

İlk açılışta panelin **PIN'ini** belirlersin (en az 6 karakter; Windows şifresi gerekmez), sonra Ayarlar penceresi gelir: depo, GitHub token (Issues: okuma-yazma) ve GitHub adın.
Ayarlar yalnız bu bilgisayarda saklanır: `%APPDATA%\TD2RaporPaneli\settings.json`.

## Neler yapılır
- **Gösterge:** rapor, öneri, görev, hesap, lisans sayıları; sürüm dağılımı ve günlük açılış (program 6.0.1+ kimliksiz sayaç),
  indirme sayıları, sunucu durumu. Kartlara tıklayınca ilgili sekme.
- **Tepside çalışma ve bildirimler:** pencereyi kapatınca tepsiye iner; yeni rapor/öneri/hesap/lisans için Windows bildirimi.
- **PIN kilidi:** belirteçler diskte PIN + DPAPI ile şifreli; 5 yanlıştan sonra artan bekleme; boşta kendiliğinden kilit;
  🔒 Kilitle düğmesi; PIN unutulursa sıfırlanır (belirteçler silinir, yeniden girilir).
- **Kendini güncelleme:** bu depodaki `panel-vX.Y.Z` sürümleri; SHA-256 doğrulanmadan kurulmaz.
- Raporları listele; tür / durum / açık-kapalı filtresi, arama (Ctrl+F), sütuna tıklayıp sıralama
- Özet sayaçları (açık, yeni, hata, istek, çalışılıyor, biten)
- Detay: açıklama, sistem bilgisi, eşya kartı, program kaydı, yorumlar (senin yanıtların yeşil)
- Durum düğmeleri: Yeni · İncelendi · Çalışılıyor · Tamamlandı · Yapılmayacak · Mükerrer (`status:*` etiketi)
- **Yanıtla:** yorum olarak yazılır, kullanıcı programdaki "Raporlarım" bölümünde görür
- Kapat / yeniden aç, GitHub'da aç (çift tık), CSV'ye aktar, F5 ile yenile (5 dakikada bir kendiliğinden)

## Test
`python tests\panel_shot.py` — sahte GitHub sunucusuyla uçtan uca test ve ekran görüntüleri (`shots\panel_*.png`).
`python tests\lock_test.py` — PIN kilidi ve kendini güncelleme. `python tests\dashboard_shot.py` — Gösterge (yerel sunucu).

