# TD2 Loot Advisor — raporlar (özel)

Bu depo **özeldir**. İki işi var:

1. **Issues:** kullanıcıların programdaki 🐞 Geri bildirim menüsünden gönderdiği hata raporları / istekler buraya düşer
   (Cloudflare Worker `td2-stats` → `/v1/reports`). Etiketler: `report`, `type:*`, `status:*`, `v*`, `lang:*`.
2. **Rapor Paneli** (`panel/`): bu issue'ları yöneten Windows programı (`TD2RaporPaneli.exe`).
   - Derleme: `panel\build_panel.bat` ya da Actions → *Build report panel* (exe + test ekran görüntüleri artifact olarak)
   - Uçtan uca video testi: Actions → *Feedback flow video* (açık depodaki programla birlikte)
   - Ayrıntılar: `panel/README.md`, kurulum: `panel/SETUP.md`

Panel açık depoda (FEDERALTURK/td2-loot-advisor) yer almaz; kullanıcılara dağıtılmaz.

