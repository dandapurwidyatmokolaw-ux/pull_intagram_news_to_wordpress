#!/bin/bash
# ==============================================================================
# Script Eksekusi Harian Otomasi Berita Instagram ke ilmuhukum.undip.ac.id
# Lokasi: /mnt/d/dev_intagram_fh/scripts/run_daily.sh
# ==============================================================================

set -e

PROJECT_DIR="/mnt/d/dev_intagram_fh"
LOG_DIR="${PROJECT_DIR}/data/logs"
mkdir -p "${LOG_DIR}"

LOG_FILE="${LOG_DIR}/daily_$(date +'%Y%m%d').log"
echo "=== MEMULAI RUN PIPELINE HARIAN [$(date '+%Y-%m-%d %H:%M:%S WIB')] ===" >> "${LOG_FILE}"

cd "${PROJECT_DIR}"

# Cek apakah feedback_server aktif, jika belum aktifkan di background
if ! pgrep -f "src/feedback_server.py" > /dev/null; then
    echo "[INFO] Menyalakan Feedback Server background daemon..." >> "${LOG_FILE}"
    PYTHONPATH=. python3 src/feedback_server.py --port 5000 >> "${LOG_DIR}/feedback_server.log" 2>&1 &
    sleep 2
fi

# Jalankan pipeline utama
export PYTHONPATH=.
python3 src/main.py >> "${LOG_FILE}" 2>&1

echo "=== PIPELINE HARIAN SELESAI [$(date '+%Y-%m-%d %H:%M:%S WIB')] ===" >> "${LOG_FILE}"
