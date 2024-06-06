@echo on
taskkill /f /FI "WINDOWTITLE eq Pixoo Script" >nul
python main.py
pause