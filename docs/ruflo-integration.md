# Ruflo ajan entegrasyonu

Bu proje için Ruflo’nun Codex yüzeyi `.agents/config.toml` ve iki yerel skill
altında kuruldu. Ana `AGENTS.md` dosyası korunmuştur; Ruflo yönergeleri onun
yerine geçmez.

Ruflo, Python uygulamasının içine gömülü bir oyun motoru değildir. Proje
geliştirme görevlerini yönlendiren bir CLI/MCP orkestrasyon katmanıdır. OCR,
canlı çeviri ve loot kararları yine TD2 Loot Advisor’ın yerel Python kodunda
çalışır. Ajanlara oyun belleği, DLL injection, anti-cheat aşma veya oyun dosyası
yazma yetkisi verilmez.

## Kontrol

```powershell
npx --yes ruflo@latest doctor --json -c node
npx --yes ruflo@latest mcp start
```

`mcp start` stdio MCP sunucusudur; uzun süreli servis olarak elle başlatılması
gerekmez. Codex, `.agents/config.toml` içindeki `ruflo` sunucusunu gerektiğinde
`cmd /c npx -y ruflo@latest mcp start` ile başlatır.

## Güvenli sınırlar

- Onay politikası `on-request`, sandbox `workspace-write` olarak ayarlanmıştır.
- Swarm otomasyonu kapalıdır; izole worktree ve açık görev olmadan ajan fan-out
  yapılmaz.
- Ağ ve model sağlayıcıları Ruflo’nun MCP/ajan görevleri için opsiyoneldir;
  ekran görüntüsü ve OCR metni varsayılan olarak uzak servise gönderilmez.
- `.codex/`, `.claude-flow/data/` ve `.claude-flow/logs/` runtime dosyalarıdır;
  Git’e eklenmez.
