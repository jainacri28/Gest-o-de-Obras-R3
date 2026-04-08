@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%venv\Scripts\python.exe"
set "APP_FILE=%PROJECT_DIR%app.py"

if not exist "%PYTHON_EXE%" (
    echo Python da virtualenv nao encontrado:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%APP_FILE%" (
    echo Arquivo app.py nao encontrado:
    echo %APP_FILE%
    pause
    exit /b 1
)

echo Abrindo aplicativo de Gestao de Obras...
echo URL esperada: http://localhost:8501
echo.

"%PYTHON_EXE%" -m streamlit run "%APP_FILE%"

if errorlevel 1 (
    echo.
    echo O aplicativo foi encerrado com erro.
    pause
)

endlocal
