@echo off
cd /d "e:\CLAUDE\BLOCKRIO\INSTA FOR YOUTUBE"
set PYTHONUTF8=1
.venv\Scripts\python.exe main.py --sync-status
.venv\Scripts\python.exe main.py --collect
.venv\Scripts\python.exe main.py --upload
