#!/usr/bin/env python3
"""Gonderilen hal (v1.8.1-paper) ile calisma agaci arasinda HAKEME GOSTERILEBILIR fark uretir.

  python3 diff_uret.py            -> ekrana ozet
  python3 diff_uret.py --md fark.md -> markdown dosyasi (cevap mektubuna ek)

Satir bazli degil CUMLE bazli calisir: makale sert sarilmis, satir diff'i
okunmaz cikar.
"""
import subprocess, sys, re, difflib, pathlib

BASE = 'v1.8.1-paper'
ROOT = pathlib.Path('/Users/alicetinkaya/Desktop/MarkLLM/MarkLLM')

def sentences(text):
    text = re.sub(r'\n(?!\n)', ' ', text)          # sert sarmayi coz
    out = []
    for block in text.split('\n\n'):
        block = block.strip()
        if not block or block.startswith('|'):
            out.append(block); continue
        out += [s.strip() for s in re.split(r'(?<=[.:?])\s+(?=[A-Z**])', block) if s.strip()]
    return [s for s in out if s]

old = subprocess.run(['git','-C',str(ROOT),'show',f'{BASE}:paper/paper.md'],
                     capture_output=True, text=True).stdout
if not old:
    sys.exit(f'HATA: {BASE} etiketinden paper.md okunamadi')
new = (ROOT/'paper/paper.md').read_text(encoding='utf-8')
a, b = sentences(old), sentences(new)
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
rows, nadd, ndel = [], 0, 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal': continue
    rows.append((tag, a[i1:i2], b[j1:j2]))
    nadd += (j2-j1) if tag in ('insert','replace') else 0
    ndel += (i2-i1) if tag in ('delete','replace') else 0
print(f'{BASE} -> calisma agaci: {len(rows)} degisiklik blogu, +{nadd} / -{ndel} cumle')
md = [f'# Changes from the submitted version ({BASE})', '',
      f'{len(rows)} change blocks. Numbers, citations and cross-references are checked by',
      '`pilot/dev_tutarlilik_kapisi.py` on every build.', '']
for k,(tag,olds,news) in enumerate(rows,1):
    md.append(f'## {k}. {tag}')
    for s in olds: md.append(f'- **removed:** {s}')
    for s in news: md.append(f'- **added:** {s}')
    md.append('')
if '--md' in sys.argv:
    out = pathlib.Path(sys.argv[sys.argv.index('--md')+1])
    out.write_text('\n'.join(md), encoding='utf-8'); print('yazildi:', out)
else:
    for k,(tag,olds,news) in enumerate(rows[:12],1):
        print(f'\n[{k}] {tag}')
        for s in olds: print('  - ', s[:150])
        for s in news: print('  + ', s[:150])
    if len(rows) > 12: print(f'\n... {len(rows)-12} blok daha (--md ile tam liste)')
