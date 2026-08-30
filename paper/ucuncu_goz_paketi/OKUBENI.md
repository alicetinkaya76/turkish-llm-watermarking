# Üçüncü-göz paketi — Language Resources and Evaluation

Bu klasör **kendi kendine yeter**. Depoya, internete veya başka bir dosyaya
ihtiyaç duymadan makalenin editör, hakem ve atıf denetimini yaptırabilirsin.

## Nasıl kullanılır

1. Bu makaleyi **hiç görmemiş** bir LLM oturumu aç. Aynı oturumda daha önce bu
   metni gördüyse denetim değersizleşir; onaylayıcı okur.
2. `UCUNCU_GOZ_PROMPT.md` dosyasını aç, içindeki **`---` ayracından sonraki
   İngilizce metni aynen kopyala** ve oturuma yapıştır. Türkçe başlık kısmını
   verme; o senin için.
3. Bu klasördeki dosyaların hepsini oturuma yükle.
4. Atıf denetimi (Rol 3) **web erişimi ister**. Erişimi olmayan bir modelde o rolü
   koşturma; koşturursan doğrulama yapmadan doğruladığını söyler.

## Klasördekiler

| dosya | ne |
|---|---|
| `UCUNCU_GOZ_PROMPT.md` | promptun kendisi |
| `paper.md` | makalenin tam metni — `paper.docx`'in kaynağı, birebir aynı içerik |
| `title_page.md` | LRE'ye ayrı yüklenen başlık sayfası |
| `cover_letter.md` | editöre giden kapak mektubu |
| `numbers.json` | makaledeki her sayının veriden üretilmiş hâli (`pilot/make_paper_numbers.py` çıktısı) |
| `detection_metrics.csv` | AUROC / TPR / güven aralığı tablolarının ham kaynağı |
| `insan_fpr_rapor.json` | S1 insan-metni yanlış-pozitif ölçümleri |
| `register2_rapor.json` | ikinci register (Vikikaynak) ölçümü |
| `s2_rapor.json` | S2 yargıç ölçümleri |
| `citation_verification.json` | **ESKİ** atıf doğrulama kaydı — prompt bunu sınanacak bir iddia olarak veriyor |
| `BENCHMARK.md` | yayımlanan kaynağın kapsamı ve bilinen sınırları |
| `DATA_LICENSE.md` | bileşen bazlı lisanslama |

## Denetçiye söylenmeyen, sana ait bağlam

Bunları prompta koymadım çünkü denetimi kirletirler. Sonucu okurken aklında olsun.

- **LRE 9 Nisan 2026'da başka bir makaleni reddetti** ("Automated Classification of
  Ottoman Court Records"). Gerekçe bilinmiyor. Denetçi bunu bilmemeli, ama sen
  editör rolünün kapsam değerlendirmesini okurken bu bilgiyle tartmalısın.
- Üç paralel gönderim kapak mektubunda beyan edildi (TALLIP-26-0165,
  NLP-2026-0191, IPM). Denetçiden bu beyanın yeterli olup olmadığını
  değerlendirmesini istedim.
- `citation_verification.json` bilerek eski hâliyle konuldu. Denetçi onu
  sınamazsa, promptun 3. rolü işlemiyor demektir; bu, denetimin kalitesini
  ölçmenin ucuz bir yolu.

## Sonucu nasıl okumalı

Denetçi bir şeyi "aşırı genelleme" diye işaretlerse **önce makaledeki cümleyi
kendin oku.** Bu makalede iddialar bilerek dar yazıldı ve önceki denetimlerde
hakemler dar yazılmış cümleleri geniş okuyup yanlış bulgu üretti. Prompt bunu
açıkça yasaklıyor ama garanti değil.
