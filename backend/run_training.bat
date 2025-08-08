@echo off
echo ========================================
echo Bell Pepper ANFIS Training Script
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Starting Improved ANFIS training...
python train_anfis_improved.py

echo.
echo Training completed!
echo Check the models/ and training_output/ directories for results.
echo.
pause 