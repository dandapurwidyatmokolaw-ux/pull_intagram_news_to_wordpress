@echo off
chcp 65001 >nul
title Pasang Penjadwalan Otomatis Jam 08.00 WIB
color 0A

echo ==============================================================================
echo        PEMASANGAN JADWAL OTOMATIS PENARIKAN BERITA INSTAGRAM FH UNDIP
echo                   JADWAL: SETIAP HARI PUKUL 08:00 WIB
echo ==============================================================================
echo.

schtasks.exe /create /tn "OtomasiBeritaInstagramFHUndip" /tr "wsl.exe -d Ubuntu -e bash -c \"cd /mnt/d/dev_intagram_fh && /bin/bash scripts/run_daily.sh\"" /sc daily /st 08:00 /f

if %errorlevel% equ 0 (
    echo.
    echo [SUKSES] Jadwal harian jam 08:00 WIB berhasil didaftarkan di Windows Task Scheduler!
    echo Nama Task: OtomasiBeritaInstagramFHUndip
    echo Waktu Eksekusi: Setiap hari pukul 08:00 WIB otomatis.
) else (
    echo.
    echo [ERROR] Gagal mendaftarkan task. Pastikan dijalankan dengan hak akses yang memadai.
)

echo.
pause