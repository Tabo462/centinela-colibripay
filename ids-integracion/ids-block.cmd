@echo off
REM Wrapper que Wazuh ejecuta como active-response.
REM Pasa el stdin (la alerta JSON) al script Python del puente.
REM %~dp0 = la carpeta donde vive este .cmd (active-response\bin).
python "%~dp0\wazuh_ar_bridge.py"
