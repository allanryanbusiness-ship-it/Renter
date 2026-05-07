@echo off
cd /d "%~dp0"
where uv >nul 2>nul
if %ERRORLEVEL%==0 (
  uv run python run_local.py %*
) else (
  python run_local.py %*
)
