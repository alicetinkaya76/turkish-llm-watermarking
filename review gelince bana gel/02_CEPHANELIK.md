# Cephanelik: hazır cevaplar

Bu makale gönderilmeden önce **beş bağımsız denetim turundan** geçti. Turlar
gerçek kusurlar buldu ve onlar düzeltildi; ama bir kısmı da **yanlış çıktı** ve
çürütüldü. Bir hakem aynı iddiayı yazarsa cevap burada hazır.

**Kullanım kuralı:** bir hakem iddiasını çürütmeden önce **kendin doğrula**. Bu
projede "denetçi haklı sandım ama değildi" ve "denetçi haksız sandım ama haklıydı"
vakalarının **ikisi de** yaşandı. §1.1 ikincisinin örneği.

---

## 1. Muhtemelen gelecek itirazlar ve cevapları

### 1.1 "Eşik belirsizliği güven aralıklarına yayılmıyor"

**İki hakem turunda geldi, ikisinde de çürüttüm — ve üçüncüsünde kısmen haklı çıktılar.**

Durum: `pilot/metrics.py` içindeki `tpr_ci_kumeli` eşiği **her bootstrap
yinelemesinde yeniden kalibre ediyor**. Bu doğru ve baştan beri öyleydi. Ama
tur 4'te ortaya çıktı ki **D3 hesabı o fonksiyonu kullanmıyordu** — önlem depoda
vardı, o hesapta çalışmıyordu. Düzeltildi: ortak istem-kümeli bootstrap, eşik her
yinelemede yeniden türetiliyor, aralık kalibrasyon örneğinin belirsizliğini
taşıyor. Hiçbir sonucun yönü değişmedi.

**Cevap:** önlemin şu an çalıştığını göster (Tablo 5 altyazısı bunu yazıyor), ve
gerekiyorsa "önceki sürümlerde D3 bunu kullanmıyordu, düzeltildi" de. Savunmacı
olma; bu bizim yakaladığımız bir kusur.

**DERS:** "önlem depoda var" ile "önlem BU hesapta çalışıyor" ayrı sorulardır.

### 1.2 "Tablo 5 seçim-sonrası bir çıkarım, doğrulayıcı sunulamaz"

Bir denetim turu bunu blocker ilan etti ve makale bir süre Tablo 5'i "exploratory
post-selection contrast" diye etiketledi. Sonra **kayıt bulundu**: `{rtt,
launder_api}` ikilisi çalışma verisinde seçilmedi.

- 18 Ağu 2026 tarihli **bağımsız pilot kohort** (Qwen2.5-3B, korpus kapısını
  geçemedi) en yıkıcı iki saldırıyı bu ikili olarak yazılı kaydetmiş
  (AUROC 0.847 / 0.889).
- Çalışma korpusu 20–21 Ağu'da üretildi; ikiliyi sabitleyen kod 23 Ağu (`4c597d0`).
- Pilot raporu, tespit tablosu ve env kaydı `audit/pilot_20260818/` olarak
  **yayımlandı** (korpus değil).

**Ana argüman:** ayrık veriyle seçim, seçen kohort kötü olsa bile Tip I hatasını
şişirmez. Pilot sıralaması gürültü olsaydı rastgele bir ikili seçilirdi ve sınama
yine geçerli olurdu, yalnız gücü düşerdi.

**Bonus (makalede yazılı):** pilot raporunun D3 bölümü "launder_api en yıkıcı"
iddiasını *kazananın-laneti* diye **geri çekmiş**. Yani pilot ikiliyi sabitliyor
ama **sırasını belirlemiyor** — Tablo 5, pilotun öngörmediği bir yönü sınıyor.
Seçim açısından mümkün olan en temiz konum.

**Kabul edilen sınır (makalede yazılı):** kayıt, çalışma verisinin kendi
sıralamasının (Tablo 4) *onayda* rol oynamadığını gösteremez, çünkü ikiliyi
sabitleyen kod skorlamadan sonra yazıldı. Bunu biz söylüyoruz, hakem söylemeden.

**Tablo 6 için mesele zaten yok:** seçim şema-*ortalaması* üzerinden, Tablo 6 ise
sıfır-toplamlı *şema kontrastı* ölçüyor — değişebilir kovaryans altında dik.

### 1.3 "Pilot ölçek, n = 24, sonuçlar zayıf"

Doğru ve makale bunu saklamıyor. Etkin n = 24 **istem**, çünkü EXP istem ve anahtar
verildiğinde deterministik: dört tohum bağımsız replikat değil. Bütün güven
aralıkları istem-kümeli bootstrap.

**Cevap çerçevesi:** bu makale sonuçlarının büyüklüğüyle değil, **ölçüm
disipliniyle** iddiada bulunuyor. Manşet bulgu (kalibrasyon hatası) 1.500 + 1.000
+ 1.500 insan penceresi üzerinde ölçüldü, 24 istem üzerinde değil — yani asıl
katkı küçük örneklemli kısımda değil. Saldırı tarafının pilot ölçekte olduğu
Sınırlılıklar'da yazılı.

### 1.4 "29 sayfa, kılavuz 18–25 diyor"

Kapak mektubunda gerekçe ve **taşıma sırası** yazılı. Editör isterse
`03_ACIK_ISLER.md` §3'teki sırayı izle. Bir tur önce 33 hücrelik tablo zaten
Online Resource 1'e taşındı.

### 1.5 "Üretken YZ kullanımı / depoda Co-Authored-By izleri"

Tam ve önden beyan edildi: YZ üç ayrı rolde kullanıldı (inceleme konusu saldırı
aracı, S2'nin iki yargıcı, kodlama/yazım asistanı). Depo geçmişindeki
`Co-Authored-By: Claude Opus 5` satırı bir **araç konvansiyonu**, yazarlık iddiası
değil; makale bunu açıkça yazıyor. Hiçbir YZ sistemi yazar değil.

**Not:** bu, hakemin *bulup* sürpriz yapabileceği bir şey değil — kapak mektubu
editörün dikkatini kendisi çekiyor.

### 1.6 "Değişebilirlik varsayımı gerekçesiz"

Makale bunu **varsayım olarak** ilan ediyor, tasarım garantisi olarak değil: iki
koşul rastgele atanmış etiketler değil, niteliksel olarak farklı iki dönüşüm.
Eşleşmenin sağladığı şey ayrı yazılı: gerçek eşlenmiş birim (aynı istem, iki
koşul) ve swap'a değişmez bir karşılaştırıcı. Yanında Wilcoxon-Pratt ve
etki büyüklüğü + kümeli aralık veriliyor; p tek dayanak değil.

### 1.7 "S2 yalnız bir kolda yargılandı"

Doğru, ön-kayıt kaynak kolu KGW olarak sabitlemişti. Sınırlılıklar'da yazılı.
**Maliyeti ölçtük:** kol başına ~5,71 USD (Opus 5), iki kol ~12 USD; kod hazır
(`--kaynak pos_EXP|pos_SynthID`). Hakem isterse revizyonda koşulabilir —
bkz. `03_ACIK_ISLER.md` §1.

### 1.8 "Dejenere AUROC hücrelerine test yok"

Bilinçli. Üç ayrı çıkarımsal işlem denendi ve **üçü de geri çekildi**
(Clopper–Pearson sınırı, istem-içi değiştirilebilirlik permütasyonu, istem düzeyi
işaret testi). Gerekçeleri `DENETIM_NOTU_geri_cekilen_cikarimlar.md`'de tam
türetimle yazılı. Onun yerine sayılmış ayrışma ve marj betimleyici olarak
veriliyor. Savunamayacağımız bir p yerine güçlü bir betimleme tercih edildi.

### 1.9 "Türkçe iddiası ne oldu?"

Ön-kayıtlı H2 (şişmenin Türkçeye özgü olduğu) sonradan eklenen **uzunluk
kontrolünü geçemedi** ve makale bunu geri çekiyor. Eşit token bütçesinde
Türkçe–İngilizce farkı saptanamıyor. Türkçenin kattığı şey *mekanizma* değil
*maruziyet*: alt-sözcük bereketi aynı okuma uzunluğunu ~2 kat token yapıyor.

Bu, makalenin lehine bir dürüstlük göstergesi — hakem "yazar kendi hipotezini
çürütmüş ve raporlamış" görür.

---

## 2. Yanlış çıkmış hakem/denetçi iddiaları (tekrar gelirse)

| İddia | Neden yanlış |
|---|---|
| "UWBench eklenmeli (yansız filigran değerlendirmesi)" | arXiv 2510.18262 UWBench **sualtı görme-dil** kıyaslamasıdır, filigranla ilgisi yok. Denetçi yanlış tanımlamış. |
| "Şu 7 dil düzeltmesi gerekli" | 4'ü zaten kapalıydı; denetçi dar yazılmış cümleleri geniş okumuştu. |
| "Tablo 5 ve 6'nın ikisi de keşifsel olmalı" | Tablo 6 için **yanlış**: seçim koşul ekseninde, kontrast şema ekseninde — dik. İki bağımsız istatistik değerlendirmesi bu öneriyi `partly_wrong` buldu. |
| "Kaynakça 42" | 43. Sayaç hatasıydı (`'' in 'ÇÖŞÜİĞ'` Python'da True → boş satırlar sayılıyordu). |

---

## 3. Bizim yakaladığımız, hakemin bulamayacağı kusurlar

Bunlar düzeltildi. Bir hakem bunlardan birini yakalarsa "zaten düzelttik" değil,
"evet, o kusur vardı ve şu sürümde düzeltildi" de.

- **Tablo 6'da gerçek sayı hatası:** ilk satır p = 0.001 basıyordu, gerçek 0.0003.
  İki bağımsız neden: biçimlendiricinin sabit `{:.3f}`'i `.round(4)`'ü eziyordu,
  ve değer `numbers.json` yerine 9 gün bayat bir rapordan kopyalanmıştı. İkisi de
  kapatıldı, kapı artık Tablo 5 ve 6'yı satır satır denetliyor.
- **D3'ün estimandı yanlıştı:** kod istem başına ortalama **ham stat** üzerinde
  koşuyordu, metin "tespit oranı" diyordu. Orana çevrilince **Bonferroni'yi geçen
  şema KGW'den EXP'e kaydı**. Kod ile metin farklı şey ölçüyordu.
- **Yayımlanan bir artefakt makaleyle çelişiyordu:** `results/summary.md` (git'te
  izleniyor) geri çekilen ham-stat D3 sonucunu yayımlamaya devam ediyordu.
- **Şekil 2'nin ekseni geçersizdi:** üç şemanın ham SD'lerini tek eksende
  karşılaştırıyordu — makalenin kendi kuralını çiğneyerek. Gerçekleşen FPR'ye
  çevrildi ve **sıralama değişti**.
- **Sekiz atıf kusuru** (Kuditipudi yanlış atıf, Rust/Liu/Bulat iddia uyuşmazlığı,
  Han/Park künye, NLLB, Pan). Dördü kimlikte değil **iddia eşlemesinde**ydi.
