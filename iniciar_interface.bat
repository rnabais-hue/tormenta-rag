@echo off
REM ============================================================
REM  RAG Tormenta20 - inicia a interface web de testes.
REM  Cuida do Ollama automaticamente. Nao precisa disparar nada
REM  mais: e so dar dois cliques neste arquivo.
REM
REM  Fechar esta janela = encerrar a interface (o servidor roda
REM  aqui dentro).
REM ============================================================

setlocal
set "OLLAMA=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "PROJ=%~dp0"

REM --- Python: usa o base do lab; se nao achar, cai para o do PATH ---
if not exist "%PYTHON%" set "PYTHON=python"

REM --- Ollama no ar? Se nao, inicia em janela minimizada ---
curl -s http://127.0.0.1:11434/api/version >nul 2>&1
if errorlevel 1 (
  echo [Ollama] Nao estava rodando. Iniciando o servidor...
  if exist "%OLLAMA%" (
    start "" /min "%OLLAMA%" serve
  ) else (
    start "" /min ollama serve
  )
) else (
  echo [Ollama] Ja esta no ar.
)

REM --- Espera o Ollama responder (ate ~20s) ---
set /a tentativas=0
:esperar
curl -s http://127.0.0.1:11434/api/version >nul 2>&1
if not errorlevel 1 goto pronto
set /a tentativas+=1
if %tentativas% geq 20 (
  echo [ERRO] Ollama nao respondeu. Abra o app Ollama e tente de novo.
  pause
  exit /b 1
)
timeout /t 1 >nul
goto esperar

:pronto
echo [Ollama] OK.
echo [Interface] Carregando indice + embedder e abrindo o navegador...
echo             (a primeira resposta na CPU pode demorar ~1 min)
cd /d "%PROJ%"
"%PYTHON%" interface.py

echo.
echo [Interface] Encerrada.
pause
