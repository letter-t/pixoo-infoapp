@echo on
taskkill /f /FI "WINDOWTITLE eq Pixoo Script" >nul
python main.py
::"C:\Users\johnc\AppData\Local\Programs\Python\Python310\python.exe"
pause