#!/bin/bash
# Revizyon sirasinda her degisiklikten sonra: tutarlilik kapisi + sayaclar + render.
set -uo pipefail
cd /Users/alicetinkaya/Desktop/MarkLLM/MarkLLM
echo "=== 1. Tutarlilik kapisi ==="
python3 pilot/dev_tutarlilik_kapisi.py; GATE=$?
echo
echo "=== 2. Sayaclar ==="
python3 - <<'PY'
import re, pathlib
t = pathlib.Path('paper/paper.md').read_text(encoding='utf-8'); L = t.split('\n')
REF = next(i for i,l in enumerate(L,1) if l.startswith('## References'))
CREDIT = [i for i,l in enumerate(L,1) if 'Conceptualization;' in l or 'curation; Writing' in l]
semi=[]
for i,l in enumerate(L,1):
    if l.startswith('|') or l.startswith('**Keywords') or i>=REF: continue
    if CREDIT and min(CREDIT)-1 <= i <= max(CREDIT)+1: continue
    inc=sum(s.count(';') for s in re.findall(r'\([^()]*\d{4}[a-z]?[^()]*\)',l))
    if l.count(';')-inc: semi.append(i)
refs=sum(1 for l in L[REF:] if l.strip() and re.match(r'[A-Za-zÇÖŞÜİĞ]',l)
         and re.search(r'\(\d{4}[a-z]?(?:, [A-Za-z]+ \d+)?\)\.',l))
a=re.sub(r'[*_`]','',re.search(r'## Abstract\s*\n(.*?)\n\*\*Keywords',t,re.S).group(1))
def order(rx):
    m={}
    for i,l in enumerate(L,1):
        if l.startswith('!['): continue
        for n in re.findall(rx,l): m.setdefault(int(n),i)
    s=sorted(m,key=lambda k:(m[k],k))
    return 'MONOTONE' if s==sorted(s) else f'OUT OF ORDER {s}'
tbl=order(r'Table (\d+)'); fig=order(r'Fig\. (\d+)')
print(f"  em dash {t.count('—')} (0 olmali) | ' – ' {t.count(' – ')} (2 = CRediT)")
print(f"  duzyazi ; {len(semi)} at {semi} (1 = APA ic ice parantez, mesru)")
print(f"  ozet {len(a.split())} kelime (150-250) | kaynak {refs}")
print(f"  Tablo {tbl} | Sekil {fig}")
PY
echo
echo "=== 3. Sayfa sayisi ==="
rm -rf /tmp/_kk && soffice --headless --convert-to pdf paper/paper.docx --outdir /tmp/_kk >/dev/null 2>&1 \
  && pdfinfo /tmp/_kk/paper.pdf | awk '/^Pages/{print "  "$2" sayfa (LRE tipik 18-25)"}'
echo
[ $GATE -eq 0 ] && echo "SONUC: kapi GECTI." || echo "SONUC: kapi BASARISIZ -- surum ALMAYIN."
exit $GATE
