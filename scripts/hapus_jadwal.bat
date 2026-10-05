@echo off
chcp 65001 >nul
title Hapus Penjadwalan Otomatis Instagram FH Undip
color 0C

echo ==============================================================================
echo         PENGHAPUSAN JADWAL OTOMATIS WINDOWS TASK SCHEDULER
echo ==============================================================================
echo.

schtasks.exe /delete /tn "OtomasiBeritaInstagramFHUndip" /f

if %errorlevel% equ 0 (
    echo.
    echo [SUKSES] Task 'OtomasiBeritaInstagramFHUndip' berhasil dihapus dari Task Scheduler.
) else (
    echo.
    echo [INFO] Task tidak ditemukan atau sudah dihapus sebelumnya.
)

echo.
pause