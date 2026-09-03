#!/bin/bash
# Revizyon dali acar ve gonderilen hali referans olarak sabitler.
#   bash revizyon_baslat.sh 1.9.0
set -euo pipefail
V="${1:?kullanim: bash revizyon_baslat.sh <yeni-surum, orn 1.9.0>}"
cd /Users/alicetinkaya/Desktop/MarkLLM/MarkLLM
BASE=v1.8.1-paper
git rev-parse -q --verify "refs/tags/$BASE" >/dev/null || { echo "HATA: $BASE etiketi yok"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "HATA: calisma agaci kirli, once commit et"; exit 1; }
BR="revizyon-v$V"
git checkout -b "$BR"
echo "dal: $BR (taban $BASE)"
echo
echo "Surum damgasini SU ALTI dosyada v$V-paper yap (kapi denetliyor):"
echo "  paper/paper.md (release tag + 'take the version tagged' + superseded listesi + kaynakca Version)"
echo "  paper/cover_letter.md  paper/title_page.md  paper/SNAPP_GONDERIM_KITI.md"
echo "  submission/SNAP-LRE/README.md  CITATION.cff  .zenodo.json  paper/citation_verification.json"
echo
echo "Superseded listesine EKLE: 22287518 (v1.8.1, gonderilen hal)"
echo
echo "Bitince:"
echo "  python3 -m pilot.make_paper_numbers"
echo "  (cd paper && NODE_PATH=/opt/homebrew/lib/node_modules node make_docx.js)"
echo "  bash 'submission/review gelince bana gel/araclar/kapi_kos.sh'"
echo "  git tag -a v$V-paper -m '...' && git push fork $BR && git push fork v$V-paper"
echo "  gh release create v$V-paper --repo alicetinkaya76/turkish-llm-watermarking --title '...' --notes '...'"
