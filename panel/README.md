# TD2 Rapor Paneli

Kullanıcıların programdaki **🐞 Geri bildirim** menüsünden gönderdiği hata raporlarını ve istekleri yönetmek için ayrı bir Windows programı.
Raporlar özel GitHub deposunda (`FEDERALTURK/td2-loot-advisor-reports`) issue olarak durur; panel onları oradan çeker.

## Çalıştırma
- **Program:** `TD2RaporPaneli.exe` (çift tıkla). Derlemek için: `panel\build_panel.bat` → `dist\panel\TD2RaporPaneli.exe`
- **Kaynaktan:** `python panel\panel.py`

İlk açılışta Ayarlar penceresi gelir: depo, GitHub token (Issues: okuma-yazma) ve GitHub adın.
Ayarlar yalnız bu bilgisayarda saklanır: `%APPDATA%\TD2RaporPaneli\settings.json`.

## Neler yapılır
- Raporları listele; tür / durum / açık-kapalı filtresi, arama (Ctrl+F), sütuna tıklayıp sıralama
- Özet sayaçları (açık, yeni, hata, istek, çalışılıyor, biten)
- Detay: açıklama, sistem bilgisi, eşya kartı, program kaydı, yorumlar (senin yanıtların yeşil)
- Durum düğmeleri: Yeni · İncelendi · Çalışılıyor · Tamamlandı · Yapılmayacak · Mükerrer (`status:*` etiketi)
- **Yanıtla:** yorum olarak yazılır, kullanıcı programdaki "Raporlarım" bölümünde görür
- Kapat / yeniden aç, GitHub'da aç (çift tık), CSV'ye aktar, F5 ile yenile (5 dakikada bir kendiliğinden)

## Test
`python tests\panel_shot.py` — sahte GitHub sunucusuyla uçtan uca test ve ekran görüntüleri (`shots\panel_*.png`).
