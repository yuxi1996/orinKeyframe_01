@echo off
setlocal
cd /d "%~dp0\.."
echo [1/4] Python version
python --version
echo [2/4] Install requirements
python -m pip install -r requirements.txt
echo [3/4] Check videos directory
if not exist videos mkdir videos
dir /b videos\*.mp4 >nul 2>nul
if errorlevel 1 echo Please put .mp4 files into orinKeyframe_01\videos and rerun benchmark.
echo [4/4] Run benchmark
python run_benchmark.py --video_dir videos
echo Results:
echo outputs\logs\benchmark.csv
echo outputs\json\benchmark_summary.json
echo outputs\reports\benchmark_report.html
