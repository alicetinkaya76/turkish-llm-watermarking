// paper/make_docx.js — paper.md -> paper.docx (gerçek Word tabloları + gömülü figürler)
//   node paper/make_docx.js
// Tablolar Markdown'dan Word tablosuna, figürler ImageRun olarak gömülür.
// Sayfa: US Letter. Başlıklar built-in HeadingLevel (TOC üretilebilsin diye).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, BorderStyle, ShadingType, PageOrientation,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const MD = fs.readFileSync(path.join(ROOT, "paper", "paper.md"), "utf8");

const SAYFA_GENIS = 12240, KENAR = 1440;          // Letter, 1" kenar (DXA)
const ICERIK = SAYFA_GENIS - 2 * KENAR;           // 9360 DXA kullanılabilir
const GRI = "5D6873", VURGU = "245E63";

// ---------- satıriçi biçim: **kalın**, *italik*, `kod` ----------
function runlar(metin, temel = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|(?<!\*)\*(?!\*)[^*]+\*(?!\*))/g;
  let son = 0, m;
  while ((m = re.exec(metin)) !== null) {
    if (m.index > son) out.push(new TextRun({ text: metin.slice(son, m.index), ...temel }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...temel }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", size: 18, ...temel }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...temel }));
    son = m.index + t.length;
  }
  if (son < metin.length) out.push(new TextRun({ text: metin.slice(son), ...temel }));
  return out.length ? out : [new TextRun({ text: "", ...temel })];
}

const P = (metin, opt = {}) => new Paragraph({
  children: runlar(metin), spacing: { after: 120, line: 276 },
  alignment: AlignmentType.JUSTIFIED, ...opt,
});

// ---------- Markdown tablosu -> Word tablosu ----------
function tabloYap(satirlar) {
  const hucre = (s) => s.trim().replace(/^\||\|$/g, "").split("|").map((x) => x.trim());
  const basliklar = hucre(satirlar[0]);
  const govde = satirlar.slice(2).map(hucre);
  const n = basliklar.length;
  // İlk sütun genelde etiket: biraz geniş; kalanlar eşit.
  const ilk = n > 3 ? Math.round(ICERIK * 0.22) : Math.round(ICERIK / n);
  const kalan = Math.floor((ICERIK - (n > 3 ? ilk : 0)) / (n > 3 ? n - 1 : n));
  const gen = n > 3 ? [ilk, ...Array(n - 1).fill(kalan)] : Array(n).fill(kalan);
  gen[n - 1] += ICERIK - gen.reduce((a, b) => a + b, 0);   // yuvarlama farkı

  // Sütun SAYISAL mı? Sağa yaslama yalnız sayısal sütunlara uygulanır --
  // ilk sürümde 0 dışındaki HER sütun sağa yaslanıyordu ve "Attack",
  // "Condition" gibi metin sütunları sağa itilmişti (render kontrolünde
  // yakalandı). Gövde hücrelerinin çoğu rakam/işaretle başlıyorsa sayısal.
  const sayisal = basliklar.map((_, i) => {
    const v = govde.map((r) => (r[i] || "").trim()).filter(Boolean);
    if (!v.length) return false;
    const say = v.filter((x) => /^[0-9+\u2212\u2013~<>-]/.test(x)).length;
    return say / v.length >= 0.6;
  });

  const satirYap = (hucreler, basmi) => new TableRow({
    tableHeader: basmi,
    children: hucreler.map((c, i) => new TableCell({
      width: { size: gen[i], type: WidthType.DXA },
      shading: basmi ? { type: ShadingType.CLEAR, fill: "EFF1F0" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({
        children: runlar(c, { size: 17, ...(basmi ? { bold: true } : {}) }),
        alignment: sayisal[i] ? AlignmentType.RIGHT : AlignmentType.LEFT,
        spacing: { after: 0 },
      })],
    })),
  });

  return new Table({
    columnWidths: gen,
    width: { size: ICERIK, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 6, color: "444444" },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: "444444" },
      left:   { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideVertical: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "DDE1DE" },
    },
    rows: [satirYap(basliklar, true), ...govde.map((r) => satirYap(r, false))],
  });
}

// ---------- figür ----------
function figurYap(rel) {
  const dosya = path.join(ROOT, "paper", rel);
  const boyut = require("child_process")
    .execSync(`python3 -c "import struct,sys;d=open('${dosya}','rb').read(33);print(struct.unpack('>II',d[16:24])[0],struct.unpack('>II',d[16:24])[1])"`)
    .toString().trim().split(" ").map(Number);
  const enMax = 5.9 * 96;                              // 5.9 inç (kenarlar içinde)
  const olcek = Math.min(1, enMax / boyut[0]);
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 180, after: 60 },
    children: [new ImageRun({
      type: "png", data: fs.readFileSync(dosya),
      transformation: { width: Math.round(boyut[0] * olcek), height: Math.round(boyut[1] * olcek) },
    })],
  });
}

// ---------- Markdown -> docx öğeleri ----------
const cocuklar = [];
const satirlar = MD.split("\n");
let i = 0;
// APA 7 kaynakçası asılı girinti ister ve iki yana yaslanmaz; "References"
// başlığından sonraki paragraflar bu biçimi alır.
let kaynakcada = false;
while (i < satirlar.length) {
  const l = satirlar[i];

  if (!l.trim()) { i++; continue; }

  // başlık
  const h = l.match(/^(#{1,3})\s+(.*)$/);
  if (h) {
    const seviye = h[1].length;
    if (seviye === 2) kaynakcada = /^References\s*$/.test(h[2].trim());
    if (seviye === 1) {
      cocuklar.push(new Paragraph({
        children: runlar(h[2], { bold: true, size: 32 }),
        alignment: AlignmentType.CENTER, spacing: { after: 200 },
      }));
    } else {
      cocuklar.push(new Paragraph({
        children: runlar(h[2], { bold: true, size: seviye === 2 ? 26 : 22 }),
        heading: seviye === 2 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
        spacing: { before: seviye === 2 ? 320 : 220, after: 120 },
      }));
    }
    i++; continue;
  }

  // figür
  const f = l.match(/^!\[[^\]]*\]\((figs\/[^)]+)\)$/);
  if (f) { cocuklar.push(figurYap(f[1])); i++; continue; }

  // tablo
  if (l.startsWith("|")) {
    const blok = [];
    while (i < satirlar.length && satirlar[i].startsWith("|")) blok.push(satirlar[i++]);
    cocuklar.push(tabloYap(blok));
    cocuklar.push(new Paragraph({ text: "", spacing: { after: 160 } }));
    continue;
  }

  // Tablo/Figür başlığı (küçük punto, ortalanmamış, gri değil — okunur)
  if (/^\*\*(Table|Figure) \d+\./.test(l)) {
    cocuklar.push(new Paragraph({
      children: runlar(l, { size: 17 }),
      spacing: { before: 60, after: 140 }, alignment: AlignmentType.LEFT,
    }));
    i++; continue;
  }

  // alıntı (>)
  if (l.startsWith("> ")) {
    cocuklar.push(new Paragraph({
      children: runlar(l.slice(2), { size: 19, color: GRI }),
      spacing: { before: 80, after: 140 }, indent: { left: 360 },
      border: { left: { style: BorderStyle.SINGLE, size: 12, color: VURGU, space: 12 } },
    }));
    i++; continue;
  }

  // liste
  const li = l.match(/^\s*[-*]\s+(.*)$/);
  if (li) {
    cocuklar.push(new Paragraph({
      children: runlar(li[1]), bullet: { level: 0 },
      spacing: { after: 80 }, alignment: AlignmentType.LEFT,
    }));
    i++; continue;
  }

  // paragraf (ardışık satırları birleştir)
  const par = [l];
  i++;
  while (i < satirlar.length && satirlar[i].trim() && !/^[#|>!]|^\s*[-*]\s|^\*\*(Table|Figure) \d+\./.test(satirlar[i])) {
    par.push(satirlar[i++]);
  }
  cocuklar.push(kaynakcada
    ? P(par.join(" "), {
        alignment: AlignmentType.LEFT,           // yaslama, uzun DOI'lerde
        indent: { left: 480, hanging: 480 },     // seyrek satır üretiyordu
        spacing: { after: 100, line: 276 },
      })
    : P(par.join(" ")));
}

const doc = new Document({
  creator: "Ali Çetinkaya",
  title: "Watermarking Turkish LLM Output",
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: SAYFA_GENIS, height: 15840, orientation: PageOrientation.PORTRAIT },
        margin: { top: KENAR, right: KENAR, bottom: KENAR, left: KENAR },
      },
    },
    children: cocuklar,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "paper", "paper.docx");
  fs.writeFileSync(out, buf);
  console.log(`yazıldı: ${out} (${(buf.length / 1024).toFixed(0)} KiB, ${cocuklar.length} öğe)`);
});
