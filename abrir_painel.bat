@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
  pause
  exit /b 1
)
echo Instalando/atualizando as bibliotecas do painel...
python -m pip install -q -r requirements.txt
echo Abrindo o painel no navegador (feche esta janela para parar)...
python -m streamlit run app.py
pause
