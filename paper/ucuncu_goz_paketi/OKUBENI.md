# Üçüncü-göz paketi

**Nasıl kullanılır:** `UCUNCU_GOZ_PROMPT.md` içindeki ayraç arasındaki metni
bağımsız bir LLM oturumuna kopyala, bu klasördeki dosyaları da ekle. Paket
artık kendi kendine yeter: makalenin kendisi de içinde.

| dosya | ne işe yarar |
|---|---|
| `UCUNCU_GOZ_PROMPT.md` | üç rollü değerlendirme promptu (editör / hakem / atıf denetçisi) |
| `paper.md` | makalenin tam metni (`paper/paper.md` ile aynı) |
| `numbers.json` | makaledeki HER sayının kaynağı — denetçi metindeki sayıları buna karşı kontrol eder |
| `citation_verification.json` | yazarların yaptığı DOI doğrulaması — denetçi "doğrulamayı doğrular" |
| `detection_metrics.csv` | tespit tablosunun ham hâli (Tablo 2 ve Figür 1'in kaynağı) |
| `insan_fpr_rapor.json` | S1 sonuçları (Tablo 6, Figür 3) |
| `register2_rapor.json` | ikinci register (Vikikaynak) sonuçları |
| `s2_rapor.json` | S2 yargıç sonuçları (Tablo 7) |

**Denetçiye söylenmesi gereken sınır:** bu paket sonuçların ÖZETLERİNİ içerir,
ham korpusu değil (384 üretilmiş metin + 3.840 saldırı metni + 2.500 insan
penceresi depoda). Denetçi sayıları çapraz kontrol edebilir ama ölçümleri
sıfırdan yeniden üretemez.
