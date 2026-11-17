## Panel 1.5.0

- **Gösterge** (ilk sekme): açık/yeni rapor, bekleyen çeviri önerisi, herkese açık ve onay bekleyen görev, hesap, aktif ve
  14 günde bitecek lisans, bugünkü açılış. Kartlara tıklayınca ilgili sekme açılır.
  - Sürüm dağılımı (son 7 gün) ve günlük açılış grafiği (son 30 gün): program 6.0.1'den itibaren kimliksiz sürüm sayacı.
  - Herkese açık depodaki sürümlerin indirme sayıları, sunucu durumu ve saatlik bakımın son çalışması.
- **Sistem tepsisi ve bildirimler**: pencere kapatılınca panel tepside çalışmaya devam eder; yeni rapor, çeviri önerisi,
  hesap ve lisans etkinleştirmesi için Windows bildirimi gösterir. Ayarlar'dan kapatılabilir.
- **PIN kilidi** (Windows şifresi gerekmez): ilk açılışta panelin kendi PIN'i belirlenir. GitHub token ve yönetici belirteci
  diskte PIN + Windows DPAPI ile iki kat şifrelenir; PIN hiçbir yerde saklanmaz. 5 yanlış denemeden sonra artan bekleme,
  boşta kalınca kendiliğinden kilit (varsayılan 10 dk), "Kilitle" düğmesi, "PIN'i unuttum" (belirteçler silinir).
- **Kendini güncelleme**: açılışta bu özel depodaki yeni panel sürümünü denetler; SHA-256 tutmazsa hiçbir şey değişmez.

