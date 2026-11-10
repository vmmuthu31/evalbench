#!/bin/bash
# One-command Qwen2.5-VL run for the annotation-leakage test (M-series Mac, 16 GB is enough).
# Usage:  cd ~/Downloads/research/qwen_leakage && bash run_all.sh        (Ollama app must be installed and running)
set -e
cd "$(dirname "$0")"
command -v ollama >/dev/null || { echo "Install Ollama first: https://ollama.com/download , open it once, then rerun."; exit 1; }
RUN=${1:-run1}
if [ ! -d "A Dataset of Digitized Student Examination Papers," ]; then
  echo "Downloading Mendeley dataset (145 MB)..."
  curl -L -o dataset.zip "https://data.mendeley.com/public-api/zip/sf3kvjwknt/download/1" && unzip -q -o dataset.zip && rm dataset.zip
fi
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip -q install pymupdf pillow
ollama pull qwen2.5vl:7b
export MENDELEY_DIR="$PWD/A Dataset of Digitized Student Examination Papers,"
for m in a1t3 e1t3 e1t5 e3b; do
  echo "=== $m ($RUN) ==="; python3 -W ignore run_ollama.py $m $RUN
done
echo "DONE. Send the folder outputs/ (ollama_qwen2.5vl_7b_$RUN) back to Claude."
