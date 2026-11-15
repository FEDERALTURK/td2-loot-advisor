# GitHub Release yetkilendirme

`Build Windows installer` içinde paketleme başarılı olup `Publish release` adımında
`403 Resource not accessible by integration` görülüyorsa sorun installer değil,
workflow tokenının release oluşturma yetkisinin olmamasıdır.

## Önerilen repository ayarı

1. GitHub repository → **Settings → Actions → General** bölümünü açın.
2. **Workflow permissions** altında **Read and write permissions** seçin.
3. Ayarı kaydedin ve başarısız çalışmayı **Re-run jobs** ile tekrar çalıştırın.

Workflow `permissions: contents: write` ve açık `token` bağlamını kullanır.

## Kuruluş politikası tokenı kısıtlıyorsa

Repository yöneticisi, yalnızca bu depo için aşağıdaki secretı ekleyebilir:

```text
TD2_RELEASE_TOKEN
```

Token için yalnızca bu repository seçilmeli ve `Contents: Read and write` izni
verilmelidir. Issues, Actions yönetimi, secrets veya administration izinleri
gerekmez.

Workflow `TD2_RELEASE_TOKEN` varsa onu, yoksa `github.token` değerini kullanır.
Secret tanımlanmadan önce workflow artifact üretebilir; release adımının başarılı
olması için repository Actions izinleri veya bu dar kapsamlı secret düzeltilmelidir.

Tokenı sohbete, workflow çıktısına veya kaynak koda yazmayın. Bu düzenleme yalnızca
GitHub Release ve asset oluşturma yetkisini ele alır; oyun belleği veya oyun
dosyalarıyla ilgili bir erişim eklemez.
