@echo off
chcp 65001 >nul
title Hentikan Server Otomasi Berita Instagram FH Undip
color 0E

echo ==============================================================================
echo           PENGHENTIAN SERVER WEBHOOK OTOMASI BERITA INSTAGRAM
echo                 FAKULTAS HUKUM UNIVERSITAS DIPONEGORO
echo ==============================================================================
echo.

where wsl >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] WSL tidak ditemukan!
    pause
    exit /b 1
)

echo [1/2] Menghentikan proses background feedback_server.py di WSL...
wsl.exe -d Ubuntu -e bash -c "pkill -f 'src/feedback_server.py' || true"

ping 127.0.0.1 -n 2 >nul

echo [2/2] Memeriksa status port 5000...
wsl.exe -d Ubuntu -e bash -c "ss -tulpn | grep 5000 >/dev/null && echo '[WARNING] Port 5000 masih terbuka' || echo '[SUKSES] Server webhook berhasil dihentikan. Port 5000 telah dilepaskan.'"
echo.

echo ==============================================================================
echo Seluruh layanan background otomasi Instagram telah dihentikan dengan aman.
echo Gunakan start.bat untuk menyalakan kembali sistem sewaktu-waktu.
echo ==============================================================================
echo.
pause