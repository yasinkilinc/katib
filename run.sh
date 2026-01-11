#!/bin/bash
# Katib Başlatma Komut Dosyası

# Proje dizinine git
cd "$(dirname "$0")"

# Sanal# Sanal ortam kontrolü
if [ -d "../.venv" ]; then
    source "../.venv/bin/activate"
elif [ -d ".venv" ]; then
    source ".venv/bin/activate"
elif [ -d "venv" ]; then
    source "venv/bin/activate"
else
    echo "⚠️  Sanal ortam (.venv) bulunamadı. Oluşturuluyor..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Ensure dependencies are up to date
echo "📦 Bağımlılıklar kontrol ediliyor..."
pip install -r requirements.txt

# Uygulamayı başlat
# Start the MCP-Native Runtime
echo "🚀 Katib (MCP-Native) başlatılıyor..."

# Pre-flight Check
echo "[*] checking syntax..."
python3 scripts/check_syntax.py
if [ $? -ne 0 ]; then
    echo "[!] Syntax Error detected. Aborting launch."
    exit 1
fi

export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 src/main.py "$@"
