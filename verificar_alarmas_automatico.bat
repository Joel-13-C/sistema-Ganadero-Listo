@echo off
echo Iniciando verificacion automatica de alarmas...
cd /d "%~dp0"
python verificacion_automatica.py
echo Verificacion completada.
