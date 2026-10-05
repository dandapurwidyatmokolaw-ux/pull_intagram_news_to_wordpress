@echo off
chcp 65001 >nul
title Sistem Otomasi Berita Instagram FH Undip
color 0B

echo ==============================================================================
echo        SISTEM OTOMASI PENARIKAN BERITA INSTAGRAM KE ILMUHUKUM.UNDIP.AC.ID
echo                 FAKULTAS HUKUM UNIVERSITAS DIPONEGORO
echo ==============================================================================
echo.

:: 1. Memeriksa ketersediaan WSL
where wsl >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] WSL (Windows Subsystem for Linux) tidak ditemukan di komputer ini!
    echo Harap pastikan WSL dan Ubuntu telah terpasang.
    echo.
    pause
    exit /b 1
)

:: 2. Memastikan Background Feedback Server Aktif di Port 5000
echo [1/3] Memeriksa status Feedback Webhook Server (Port 5000)...
wsl.exe -d Ubuntu -e bash -c "pgrep -f 'src/feedback_server.py' >/dev/null || (cd /mnt/d/dev_intagram_fh && export PYTHONPATH=. && nohup python3 src/feedback_server.py --port 5000 > data/logs/feedback_server.log 2>&1 &)"

ping 127.0.0.1 -n 3 >nul
wsl.exe -d Ubuntu -e bash -c "curl -s http://localhost:5000/health >/dev/null && echo '[OK] Feedback Webhook Server aktif dan berjalan di http://localhost:5000' || echo '[WARNING] Feedback Server sedang bersiap...'"
echo.

:: 3. Menjalankan Pipeline Utama (Scraper -> AI Narrator -> Email Kurator -> WP Publish)
echo [2/3] Menjalankan Pipeline Harian Penarikan Berita Instagram...
echo ------------------------------------------------------------------------------
wsl.exe -d Ubuntu -e bash -c "cd /mnt/d/dev_intagram_fh && export PYTHONPATH=. && python3 src/main.py"
echo ------------------------------------------------------------------------------
echo.

:: 4. Menu Interaktif Operasional
:MENU
echo ==============================================================================
echo                            MENU PILIHAN OPERASIONAL
echo ==============================================================================
echo  [1] Jalankan Ulang Pipeline (Tarik Postingan Baru Hari Ini)
echo  [2] Buka Halaman Status Server di Browser (http://localhost:5000/health)
echo  [3] Buka Pratinjau Email Kurasi Terbaru di Browser
echo  [4] Buka Folder Data, Media, dan Log di Windows Explorer
echo  [5] Hentikan Server Webhook (Stop Server)
echo  [0] Keluar (Biarkan Server Tetap Berjalan di Background)
echo ==============================================================================

choice /c 123450 /n /m "Pilih opsi [1-5 atau 0]: "
set opt=%errorlevel%

if "%opt%"=="1" (
    echo.
    echo Menjalankan ulang pipeline...
    wsl.exe -d Ubuntu -e bash -c "cd /mnt/d/dev_intagram_fh && export PYTHONPATH=. && python3 src/main.py"
    echo.
    goto MENU
)

if "%opt%"=="2" (
    start http://localhost:5000/health
    goto MENU
)

if "%opt%"=="3" (
    wsl.exe -d Ubuntu -e bash -c "LATEST=$(ls -t /mnt/d/dev_intagram_fh/data/email_previews/*.html 2>/dev/null | head -n 1); if [ -n \"$LATEST\" ]; then wslpath -w \"$LATEST\"; fi" > "%TEMP%\latest_preview.txt"
    set /p PREVIEW_PATH=<"%TEMP%\latest_preview.txt"
    if defined PREVIEW_PATH (
        start "" "%PREVIEW_PATH%"
    ) else (
        echo [INFO] Belum ada file pratinjau email di folder data\email_previews.
    )
    goto MENU
)

if "%opt%"=="4" (
    explorer "D:\dev_intagram_fh\data"
    goto MENU
)

if "%opt%"=="5" (
    echo.
    call "%~dp0stop.bat"
    goto MENU
)

if "%opt%"=="6" (
    echo.
    echo Server webhook tetap aktif di background port 5000.
    echo Gunakan stop.bat jika ingin menghentikan server sewaktu-waktu.
    ping 127.0.0.1 -n 3 >nul
    exit /b 0
)

goto MENU