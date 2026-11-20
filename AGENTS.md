# TD2 Loot Advisor — AI Ajan Kuralları ve İş Akışı Sözleşmesi

Bu dosya, TD2 Loot Advisor projesinde çalışan tüm AI ajanları için bağlayıcı
çalışma kurallarını tanımlar. Kod değişikliği, test, repo bakımı veya yayın
hazırlığı başlamadan önce bu kurallar dikkate alınır.

## Değişmez güvenlik ve gizlilik sınırları

1. Oyun belleği **okunmaz veya yazılmaz**. `ReadProcessMemory` ve
   `WriteProcessMemory` kullanılamaz.
2. DLL injection, anti-cheat aşma, oyun verisi değiştirme veya hile işlevi
   önerilmez ve koda eklenmez.
3. Ekran yakalama ve OCR, varsayılan olarak tamamen yerelde çalışır. Ekran
   görüntüsü veya OCR metni kullanıcıdan açıkça izin alınmadan uzak bir hizmete
   gönderilmez.
4. Exotic, Named, Prototype ve kilitli eşyalar hiçbir zaman otomatik silme,
   kırma veya `DISMANTLE` kararına dahil edilmez. Düşük OCR güveninde sonuç
   `REVIEW` olarak kalır.
5. GitHub'a hata raporu göndermeden önce kullanıcıya maskelenmiş bir önizleme
   sunulur. Kullanıcının açık onayı olmadan hata kaydı gönderilmez.
6. Kod yazımı, yerel testler, commit ve push iş akışın parçası olarak
   yapılabilir. Ancak public GitHub Release, public tag veya installer/APK
   üretimi ve yayını için kullanıcıdan açık onay zorunludur. Yayın öncesinde
   şu soru sorulur ve açık `Evet` yanıtı beklenir:

   ```text
   Yeni Güncellemeyi Yayınlamak İster misiniz? (vX.Y.Z) — Evet / Hayır
   ```

## Ajan rolleri ve tetikleyiciler

### `python-core-developer`

**Tetikleyici:** `app.py`, `engine.py`, `stash.py` veya `gamedata.py`.

- PEP 8 ve mümkün olduğu yerde `black` biçimlendirmesine uy.
- `app.py` renk paleti değişikliklerini `ui_theme.PALETTES` üzerinden doğrula.
- Küçük, güvenli ve mevcut kullanıcı davranışını koruyan değişiklikleri tercih et.

### `i18n-ocr-translator`

**Tetikleyici:** `livetranslate.py`, `ocr_backend.py` veya `lang/`.

- On dilli çeviri altyapısını koru.
- `blocks_from_lines()` dönüşünü her zaman `(metin, kutu, güven)` üçlüsü olarak
  koru.
- Dil dosyalarındaki eksik `lt.partial` anahtarlarını tamamla.
- Yerinde çeviri overlay'i fare/tıklama olaylarını engellememelidir.

### `ui-theme-expert`

**Tetikleyici:** `td2app/ui/` altındaki görsel modüller.

- Varsayılan Kaivolt (lacivert/mor) HUD estetiğini koru.
- `SafeTrail` fare izi efektlerinin tıklamayı engellemesini önle.
- `Canvas.lower()` çağrılarına dayanmak yerine savunmacı nesne varlık ve yaşam
  döngüsü kontrolleri uygula.
- Küçük pencere ve düşük kaynaklı bilgisayarlarda akıcılığı öncele.

### `ci-test-automator`

**Tetikleyici:** `tests/` veya `.github/workflows/`.

- Yeni sekme eklendiğinde `test_stability_widgets.py` içindeki `pages==15`
  beklentisini bilinçli biçimde güncelle.
- Test izolasyonunu koru: testleri toplu çalıştırmak yerine gerektiğinde
  `python -B tests/<dosya>` biçiminde tekil çalıştır.
- Görsel/OCR/overlay testlerinde kanıt ile varsayımı ayır; flaky testi sadece
  susturmak için zayıflatma.

### `ops-git-janitor`

**Tetikleyici:** backlog, `.gitignore` veya repo temizliği.

- Runtime ve kullanıcı verilerini commit etme: `builds.json`, `stash.json`,
  `progress.json`, `tasks.json`, `sessions.json`, `.bak` dosyaları ve kişisel
  loglar takip dışı kalmalıdır.
- `builds.json` zaten takipteyse, yalnız açık repo temizliği görevi kapsamında
  Git geçmişini yeniden yazmadan `git rm --cached` ile takipten çıkar.
- `sessions.json` dosyasını `.gitignore` içinde açıkça koru.
- Silme, geri alma veya üzerine yazma işlemlerinden önce hedefi doğrula.

## Standart çalışma akışı

1. Her kullanıcı görevinin ilk kullanıcıya açık satırında aktif rolü belirt:
   `[Active Agent: <rol>]`.
2. Kod yazmadan önce kısa bir `Plan:` başlığı altında uygulanacak adımları
   maddeler halinde açıkla.
3. Değişiklikten önce `git status` kontrolü yap; ilgisiz kullanıcı değişikliklerini
   koru.
4. En küçük güvenli değişikliği uygula ve ilgili yerel testleri çalıştır.
5. Sonuçta hangi testin çalıştığını, neyin kanıtlandığını ve hangi ortam düzeyi
   doğrulamanın hâlâ gerektiğini açıkça bildir.
6. Public yayın için bu dosyadaki yayın onayı sorusunu sor; açık `Evet` olmadan
   release, tag veya installer/APK yayınlama.

## Uygulama doğruluk ilkeleri

- Canlı çeviri veya overlay sorunu için önce OCR çıktısı, yakalama alanı,
  pencere koordinatları ve render kanıtını topla; boş/siyah kutu sorununu
  varsayımla çözülmüş sayma.
- HDR durumu yalnız doğrulanabilir oyun ayarı ve ekran yakalama verisiyle
  değerlendirilir; tahmin yoluyla kullanıcıya HDR uyarısı gösterme.
- Loot karar sistemi belirsizlikte korumacı davranır: otomatik imha yerine
  inceleme, kullanıcı onayı ve açıklanabilir gerekçe kullan.
- Oyun kurulum yolu ve ayar dosyaları yalnız okunur biçimde incelenir; oyun
  ayarını değiştirecek bir işlem için kullanıcıya açık bilgi ve onay verilir.

### Test verisi

- Testler `meta/` altındaki bot tarafından güncellenen dosyalardan sabit kimlik,
  başlık veya metin kullanamaz. Davranış testleri kendi fixture'ını oluşturur;
  canlı dosyalar yalnız şema/geçerlilik testlerinde kullanılır.

### Dal ve etiket hijyeni

- Her sürüm dalı yayından sonra `main`'e geri birleştirilir.
- Yayınlanmış bir etiket başka bir commit'e taşınmaz; gerekirse yeni yama
  sürümü açılır.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## UI / UX Pro Max (mandatory for interface work)

For every task that designs, implements, reviews, or fixes the User Interface,
design system, visual theme, UI components or controls, navigation, typography,
accessibility, responsive layout, charts, interaction states, or UI animation,
use the installed `ui-ux-pro-max` skill and the relevant companion skill from
`.agents/skills/` before changing code. The main skill is
`.agents/skills/ui-ux-pro-max/SKILL.md`; its local search tool is
`.agents/skills/ui-ux-pro-max/scripts/search.py`.

- For a new or system-wide design direction, run the skill's `--design-system`
  search. For a focused component or UX issue, search the matching domain; for
  stack guidance, use `--stack` as documented by the skill.
- Use companion skills such as `design-system`, `ui-styling`, `design`, and
  `brand` when they match the requested work.
- Treat search results as guidance: preserve the existing Kaivolt theme tokens,
  project behavior, accessibility, and performance constraints unless the user
  explicitly asks to change them. Do not apply a whole-app redesign to a
  component-scoped request.
- Verify the changed UI states and layout with the relevant local checks, and
  state which visual/runtime behavior was actually verified.
