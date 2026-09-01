# Üçüncü-göz paketi — tur 4 (ODAKLI), Language Resources and Evaluation

**Sürüm damgası: `v1.4.0-paper / sha256 8033571d`, 2026-09-01.**

Bu klasör kendi kendine yeter. Depoya, internete veya başka bir dosyaya ihtiyaç
duymadan denetimi yaptırabilirsin.

## Bu tur neden farklı

Önceki üç tur makaleyi baştan sona inceledi ve **doyum noktasına yaklaştı**: son
turda önerilen yedi dil düzeltmesinin dördü zaten kapalıydı, bir kaynak önerisi de
tamamen yanlış makaleye aitti (aşağıya bak). Dördüncü bir tam tur çoğunlukla aynı
yanlış pozitifleri üretirdi.

Bu tur bunun yerine **yalnızca son turda değişeni** denetliyor, çünkü risk orada:

1. Bir **estimand değişti** ve manşet sonuç KGW'den EXP'e kaydı.
2. **Altı yeni kaynak** ve onlarla gelen yeni nesir girdi.
3. Makale **1.754 kelime kısaltıldı** (36 → 32 sayfa).

## Nasıl kullanılır

1. Bu makaleyi **hiç görmemiş** bir LLM oturumu aç. Aynı oturum metni daha önce
   gördüyse denetim değersizleşir; onaylayıcı okur.
2. `UCUNCU_GOZ_PROMPT_YAPISTIR.md` dosyasının tamamını kopyala, oturuma yapıştır.
   (Paketteki `UCUNCU_GOZ_PROMPT.md` Türkçe başlık da içerir; denetçiye onu değil,
   yapıştır sürümünü ver.)
3. Bu klasördeki dosyaların hepsini, `kod/` dahil, oturuma yükle.
   **`paper_ONCEKI_v1.3.0.md` şart** — Rol 3 sıkıştırmayı ancak karşılaştırarak
   denetleyebilir.
4. **Rol 4 web erişimi ister.** Erişimi olmayan bir modelde o rolü koşturma;
   koşturursan doğrulama yapmadan doğruladığını söyler.

## Rapor gelince ilk iş

**Raporun başında `v1.4.0-paper / sha256 8033571d` damgasını ara.** Yoksa veya
tutmuyorsa denetçi eski bir kopya okumuştur. Bir turda tam olarak bu oldu: beş
bulgu zaten düzeltilmişti.

## Klasördekiler

| dosya | ne |
|---|---|
| `UCUNCU_GOZ_PROMPT.md` | promptun kendisi (Türkçe başlıklı) |
| `paper.md` | **v1.4.0** makale metni — `paper.docx`'in kaynağı, birebir aynı |
| `paper_ONCEKI_v1.3.0.md` | **v1.3.0** metni — sıkıştırma denetimi için kıyas |
| `title_page.md` | LRE'ye ayrı yüklenen başlık sayfası |
| `cover_letter.md` | kapak mektubu (yeni "On length" paragrafı içinde) |
| `numbers.json` | makaledeki her sayının veriden üretilmiş hâli |
| `detection_metrics.csv` | AUROC / TPR / güven aralığı tablolarının ham kaynağı |
| `insan_fpr_rapor.json` | S1 insan-metni yanlış-pozitif ölçümleri |
| `register2_rapor.json` | ikinci register (Vikikaynak) ölçümü |
| `s2_rapor.json` | S2 yargıç ölçümleri |
| `citation_verification.json` | atıf denetim kaydı — **sınanacak iddia**, kanıt değil |
| `DENETIM_NOTU_geri_cekilen_cikarimlar.md` | geri çekilen üç çıkarımın tam türetimi |
| `BENCHMARK.md` | yayımlanan kaynağın kapsamı ve bilinen sınırları |
| `DATA_LICENSE.md` | bileşen bazlı lisanslama |
| `kod/metrics.py` | kümeli bootstrap, eşik kalibrasyonu, **`d3_istem_duzeyi`** |
| `kod/dev_tutarlilik_kapisi.py` | geri çekilmiş nicelik sızarsa sürümü düşüren kapı |
| `kod/dev_dejenere_kanit.py` | dejenere hücrelerde ayrışma ve marj |
| `kod/dev_h2_token.py` | token-uzunluğu denetimi (H2'yi geçersiz kılan koşu) |
| `kod/dev_anahtar_supurme.py` | sekiz anahtarlı null süpürmesi |

## Denetçiye sorulmayan, çünkü ZATEN DOĞRULADIM

Bunları prompta koymadım; denetçi yine bulursa bilgin olsun diye buradalar.

- **Permütasyon testi kaba kuvvetle sınandı.** DP tabanlı `_tam_isaret_permutasyon_p`
  ile 2^n tam numaralandırma birebir aynı sonucu veriyor (fark 0.00e+00, üç şemada
  da). Test çift yanlı, yani muhafazakâr. Aynı tohumla deterministik.
- **Çapraz göndergeler sağlam.** 20 bölüm, 11 tablo, 3 şekil; kırık bölüm
  göndergesi yok, atıfsız tablo/şekil yok, tanımsız atıf yok.
- **Sayılar `numbers.json` ile tutuyor** ve `kod/dev_tutarlilik_kapisi.py` bunu her
  koşuda kontrol ediyor (negatif kontrolle sınandı: gerçekten yakalıyor).

Denetçinin asıl işi bunlar değil; **null'un savunulabilirliği** ve **sıkıştırmanın
ne düşürdüğü**.

## Denetçiye söylenmeyen, sana ait bağlam

- **LRE 9 Nisan 2026'da başka bir makaleni reddetti** ("Automated Classification of
  Ottoman Court Records"). Gerekçe bilinmiyor. Denetçi bunu bilmemeli, ama sen
  editör rolünün kapsam değerlendirmesini okurken bu bilgiyle tartmalısın.
- Üç paralel gönderim kapak mektubunda beyan edildi (TALLIP-26-0165,
  NLP-2026-0191, IPM).
- Uzunluk kararı bilinçli: 32 sayfa, kılavuz 18-25 diyor. Daha fazla kesmek üç
  denetim turunun **eklettiği** kapsam niteleyicilerini silmek olurdu. Kapak
  mektubu bunu editöre açıyor ve taşınacak malzemeyi adıyla listeliyor.

## Sonucu nasıl okumalı

**Bir bulguyu uygulamadan önce üç şeyi kontrol et.**

1. Denetçi **"aşırı genelleme"** derse önce makaledeki cümleyi kendin oku. Bu
   makalede iddialar bilerek dar yazıldı; geçen tur önerilen yedi dil
   düzeltmesinin **dördü zaten kapalıydı** — denetçi dar cümleleri geniş okumuştu.
2. Denetçi bir istatistiksel önlemin **"eksik"** olduğunu söylerse `kod/` içinden
   doğrula. Bu iddia iki ayrı turda geldi ve iki kere de yanlıştı
   (`metrics.py`'deki `tpr_ci_kumeli` eşiği her bootstrap yinelemesinde yeniden
   kalibre ediyor).
3. Rol 4'te **uydurma referansa** dikkat. Geçen tur denetçi "UWBench"i yansız
   filigran değerlendirmesi diye önerdi; arXiv 2510.18262 UWBench **sualtı
   görme-dil kıyaslamasıdır**, filigranla hiçbir ilgisi yok. Önerilen her LRE
   makalesinin DOI'sini tıklayıp gerçekten var olduğunu ve söylenen şeyi
   söylediğini doğrulamadan hiçbirini ekleme.

**Buna karşılık Rol 2 ve Rol 3'ü ciddiye al.** Rol 2 üç kez yanlış kurduğum bir
akıl yürütmenin dördüncü hâlini sınıyor; Rol 3 ise bu sürümdeki en olası kusuru
arıyor — sıkıştırma sırasında bir kapsam niteleyicisinin sessizce düşmüş olması.
