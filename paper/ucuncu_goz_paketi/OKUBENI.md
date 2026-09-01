# Üçüncü-göz paketi — Language Resources and Evaluation

**Sürüm damgası: `v1.4.0-paper / sha256 8033571d`, 2026-09-01.**

Bu klasör kendi kendine yeter. Depoya, internete veya başka bir dosyaya ihtiyaç
duymadan makalenin editör, hakem, atıf ve dergi-içi kaynak denetimini
yaptırabilirsin.

## Nasıl kullanılır

1. Bu makaleyi **hiç görmemiş** bir LLM oturumu aç. Aynı oturum metni daha önce
   gördüyse denetim değersizleşir; onaylayıcı okur.
2. `UCUNCU_GOZ_PROMPT.md` dosyasını aç, içindeki **`---` ayracından sonraki
   İngilizce metni aynen kopyala** ve oturuma yapıştır. Türkçe başlık kısmını
   verme.
3. Bu klasördeki dosyaların hepsini, `kod/` dahil, oturuma yükle.
4. **Rol 3 ve Rol 4 web erişimi ister.** Erişimi olmayan bir modelde bu iki rolü
   koşturma; koşturursan doğrulama yapmadan doğruladığını söyler.

## Rapor gelince ilk iş

**Raporun başında `v1.4.0-paper / sha256 8033571d` damgasını ara.** Yoksa veya tutmuyorsa denetçi eski
bir kopya okumuştur ve bulguların bir kısmı çoktan kapanmış işleri tekrar eder.
Geçen turda tam olarak bu oldu: beş bulgu zaten düzeltilmişti.

## Klasördekiler

| dosya | ne |
|---|---|
| `UCUNCU_GOZ_PROMPT.md` | promptun kendisi |
| `paper.md` | makalenin tam metni — `paper.docx`'in kaynağı, birebir aynı içerik |
| `title_page.md` | LRE'ye ayrı yüklenen başlık sayfası |
| `cover_letter.md` | editöre giden kapak mektubu |
| `numbers.json` | makaledeki her sayının veriden üretilmiş hâli |
| `detection_metrics.csv` | AUROC / TPR / güven aralığı tablolarının ham kaynağı |
| `insan_fpr_rapor.json` | S1 insan-metni yanlış-pozitif ölçümleri |
| `register2_rapor.json` | ikinci register (Vikikaynak) ölçümü |
| `s2_rapor.json` | S2 yargıç ölçümleri |
| `citation_verification.json` | iki atıf denetiminin kaydı — **sınanacak iddia**, kanıt değil |
| `BENCHMARK.md` | yayımlanan kaynağın kapsamı ve bilinen sınırları |
| `DATA_LICENSE.md` | bileşen bazlı lisanslama |
| `kod/metrics.py` | kümeli bootstrap, eşik kalibrasyonu, AUROC/TPR hesapları |
| `kod/dev_dejenere_kanit.py` | dejenere hücrelerde ayrışma, marj, p-değeri |
| `kod/dev_h2_token.py` | token-uzunluğu denetimi (H2'yi geçersiz kılan koşu) |
| `kod/dev_anahtar_supurme.py` | sekiz anahtarlı null süpürmesi |

**`kod/` neden var:** geçen turda denetçi, zaten kurulu olan bir yöntemi ("eşik
belirsizliği güven aralığına taşınıyor mu") koda bakmadığı için "eksik" diye
bildirdi. Artık bakabilir; prompt da bakmasını şart koşuyor.

## Denetçiye söylenmeyen, sana ait bağlam

Bunlar prompta konmadı çünkü denetimi kirletirler. Sonucu okurken aklında olsun.

- **LRE 9 Nisan 2026'da başka bir makaleni reddetti** ("Automated Classification
  of Ottoman Court Records"). Gerekçe bilinmiyor. Denetçi bunu bilmemeli, ama sen
  editör rolünün kapsam değerlendirmesini okurken bu bilgiyle tartmalısın.
- Üç paralel gönderim kapak mektubunda beyan edildi (TALLIP-26-0165,
  NLP-2026-0191, IPM). Denetçiden bu beyanın yeterliliğini değerlendirmesi
  istendi.
- `citation_verification.json` iki turun kaydı: 30 Ağustos'ta koşturduğumuz
  18-ajanlı denetim (8 kusur) ve ardından gelen üçüncü-göz turu (9 kusur daha).
  Prompt bunu "sınanacak iddia" diye veriyor. Denetçi kaydı sorgusuz onaylarsa
  3. rol işlemiyor demektir — denetimin kalitesini ölçmenin ucuz yolu.

## Sonucu nasıl okumalı

**Bir bulguyu uygulamadan önce iki şeyi kontrol et.**

Birincisi: denetçi "aşırı genelleme" derse **önce makaledeki cümleyi kendin oku.**
Bu makalede iddialar bilerek dar yazıldı ve önceki turlarda hakemler dar yazılmış
cümleleri geniş okuyup yanlış bulgu üretti. Prompt bunu yasaklıyor ama garanti
değil.

İkincisi: denetçi bir istatistiksel önlemin "eksik" olduğunu söylerse
**`kod/` içinden doğrula.** Bu iddia iki ayrı turda geldi ve iki kere de yanlıştı
(`metrics.py` içindeki `tpr_ci_kumeli` eşiği her bootstrap yinelemesinde yeniden
kalibre ediyor).

Rol 4'te (LRE kaynakları) dikkat edilecek şey farklı: **uydurma referans.** Bir
LLM'den belirli bir dergiden kaynak istemek, halüsinasyona en açık istektir.
Önerilen her LRE makalesinin DOI'sini tıklayıp gerçekten var olduğunu ve
söylenen şeyi söylediğini doğrulamadan hiçbirini ekleme.
