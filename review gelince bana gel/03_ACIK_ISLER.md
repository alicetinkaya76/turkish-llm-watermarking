# Açık işler: revizyonda ne yapılabilir

Sıralama, bir hakemin isteme olasılığına göre.

## 1. S2'yi diğer iki kola genişlet — HAZIR, ~12 USD

**En olası revizyon isteği.** Anlam korunumu yalnız KGW kolunda yargılandı
(ön-kayıt öyle sabitlemişti); EXP ve SynthID satırları bir kol-arası taşınabilirlik
varsayımına dayanıyor. Sınırlılıklar bunu yazıyor.

Altyapı hazır:

```bash
cd ~/Desktop/MarkLLM/MarkLLM
.venv/bin/python -m pilot.dev_s2_fayda --kaynak pos_EXP
.venv/bin/python -m pilot.dev_s2_fayda --kaynak pos_SynthID
```

- Ayrı dosyaya yazar (`results_insan/s2_fayda_pos_*.jsonl`), KGW kolunun
  çıktısına dokunmaz.
- Kalibrasyon çiftleri tekrarlanmaz (yargıç güvenilirliği kol-bağımsız, KGW'de
  ölçüldü).
- **Ölçülen maliyet:** EXP kolunda 3 çiftlik deneme = 6 Opus çağrısı, 0,107 USD →
  tam koşu ~5,71 USD/kol.
- API anahtarı `.env`'de (`ANTHROPIC_API_KEY`, `GROQ_API_KEY`). ⚠️ **HPC'ye
  kopyalanmaz** — bu yüzden S2 ve `launder_api` yerelde koşar.

Koştuktan sonra: `make_paper_numbers` → tablo yenilenir → kapı → yeni sürüm.

⚠️ Kısmi çıktılar `.gitignore`'da. Tam koşu bitmeden sürüme girmesinler.

## 2. Zenodo erişim jetonunu döndür — SENDE, gönderimi bloke etmez

Oturum dökümüne bir Zenodo `access_token` düştü (webhook teslimat URL'sini
bastırdım, benim hatam). Ayrıca son üç sürümde webhook ilk teslimatta 403/500
verip ikincide 202 döndü — jeton reddediliyor olabilir.

**Yapılacak:** zenodo.org → Applications → Personal access tokens → jetonu sil,
yenisini üret. Sonra GitHub'da depo webhook'unu kaldır, Zenodo'nun GitHub
sekmesinden depoyu kapat-aç (hook'u yeni jetonla o kurar).

Yapılmazsa: mevcut DOI'ler çalışır, ama **bir sonraki sürüm DOI almayabilir**.

## 3. Uzunluk kısaltma sırası (editör isterse)

Kapak mektubunda yazılı sıra. Zaten yapılan: 33 hücrelik tablo → Online Resource 1.

1. Sekiz-anahtar süpürmesinin ayrıntısı → aralığı ve sonucu makalede kalsın
2. Veri Erişilebilirliği'ndeki sürüm/zaman damgası tartışması + uzun lisans
   anlatısı → erişim yolu ve "lisans tekdüze değil" uyarısı kalsın
3. Keşifsel yeniden-skorlama ve kirlenme gözlemleri

**Baskı altında bile çıkarılmayacak:** §4.3'ün uzunluk kontrolü. Türkçe–İngilizce
karşılaştırmasının token-bütçesi karışıklığı diye okunmasını o engelliyor ve
ön-kayıtlı bir sonucu değiştiren şey o.

## 4. Zenodo v1.1.0 lisans alanı — kozmetik

Yayımlanmış `22168553` kaydının lisans alanı hâlâ `cc-by-sa-4.0`; doğrusu
`other-open` (tek alan Apache + CC BY-SA + CC BY-NC + CC0 + ODC-BY'yi ifade
edemiyor). Zenodo arayüzünden üst-veri düzenlenebilir, DOI değişmez. Sonraki
sürümlerde doğru.

## 5. Ön-kayıt zaman damgası — yapısal, düzeltilemez

Ön-kayıt commit'leri 23–25 Ağustos diyor ama depo GitHub'a 29 Ağustos'ta açıldı.
Yani **hiçbir üçüncü taraf kaydı ön-kaydı veriden ayırmıyor**; hash'ler içeriği ve
sırayı sabitliyor, duvar saatini değil. Makale bunu açıkça yazıyor.

Geçmişe dönük düzeltilemez. **Bundan sonraki projelerde ön-kayıt, kayıt anında
üçüncü taraf ankrajı almalı** (OSF, arXiv, ya da hemen push edilmiş bir GitHub
deposu).

---

## Reddedilirse: sıradaki dergiler

Bu makale LRE'ye özel ayarlandı (APA 7, ondalık başlıklar, Statements and
Declarations, özet 249 kelime). Başka dergiye giderken biçim dönüşümü gerekir.

| Aday | Not |
|---|---|
| **Computer Speech & Language** (Elsevier) | Kapsam uyumlu. **Ama** daha önce "saf NLP kabul etmiyor" diye aday havuzundan çıkarılmıştı — yeniden doğrula. |
| **TALLIP** (ACM) | Az-kaynaklı dil kapsamı tam uyumlu. **Çakışma:** TALLIP-26-0165 hâlâ inceleme altında. |
| **Natural Language Processing** (Cambridge) | ULAKBİM anlaşması APC'yi sıfırlıyor. **Çakışma:** NLP-2026-0191 inceleme altında. |
| **LREC / COLING** (konferans) | Kaynak makalesi için doğal ev, ama dergi değil. |
| **PeerJ Computer Science** | Açık erişim, APC var, fon yok. |

⚠️ **İlk iki tercihte de aktif gönderimin var.** Üçü de Türkçe NLP → aynı dar
hakem havuzu. Yeni gönderim planlarken bu listeye bak; bu çakışma bu projede iki
kez gözden kaçtı.
