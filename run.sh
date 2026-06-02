#!/bin/bash
# Katib Başlatma Komut Dosyası

# Hata durumunda durma (ama sanal ortam kontrolü gibi yerlerde esnek olabiliriz)
set -e

# Proje dizinine git
cd "$(dirname "$0")"

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Katib Başlatılıyor...${NC}"

# 1. FFmpeg Kontrolü (Ses işleme için kritik)
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[!] Hata: FFmpeg bulunamadı.${NC}"
    echo "Lütfen yükleyin: brew install ffmpeg"
    exit 1
fi

# 2. Sanal Ortam Kontrolü ve Aktivasyonu
VPATH=""
if [ -d ".venv" ]; then
    VPATH=".venv"
elif [ -d "venv" ]; then
    VPATH="venv"
fi

if [ -z "$VPATH" ]; then
    echo -e "${YELLOW}⚠️  Sanal ortam bulunamadı. Oluşturuluyor (.venv)...${NC}"
    python3 -m venv .venv
    VPATH=".venv"
fi

source "$VPATH/bin/activate"
echo -e "${GREEN}[✓] Sanal ortam aktif: $VPATH${NC}"

# 3. Bağımlılıkların Yüklenmesi (Sessiz modda, sadece hata varsa basar)
echo -e "${YELLOW}📦 Bağımlılıklar senkronize ediliyor...${NC}"
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Bağımlılık yükleme hatası!${NC}"
    exit 1
fi

# 4. Syntax Kontrolü
echo -e "${YELLOW}[*] Kod sözdizimi kontrol ediliyor...${NC}"
python3 scripts/check_syntax.py
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Syntax Hatası tespit edildi. Başlatılamıyor.${NC}"
    exit 1
fi

# 5. Başlatma
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo -e "${GREEN}[✓] Hazır. Uygulama başlatılıyor...${NC}"

# Uygulamayı çalıştır ve çıkış kodunu yakala
set +e
python3 src/main.py "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}[!] Katib bir hata ile kapandı (Kod: $EXIT_CODE).${NC}"
    echo "Log dosyasını inceleyin: logs/katib.log"
else
    echo -e "${GREEN}[✓] Katib başarıyla sonlandı.${NC}"
fi
