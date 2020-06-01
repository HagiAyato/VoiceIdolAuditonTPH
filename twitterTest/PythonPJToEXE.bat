rem ↓%~dp0=カレントディレクトリ
cd %~dp0
rem .exeに変換
py -m PyInstaller twitterTest.py --onefile
rem distフォルダに移動
rem move dist\twitterTest.exe twitterTest.exe
pause