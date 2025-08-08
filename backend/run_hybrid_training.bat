@echo off
echo ========================================
echo Bell Pepper Hybrid Training System
echo ========================================
echo.
echo This system offers three training approaches:
echo 1. ANFIS (Fuzzy Logic) - Fast, interpretable
echo 2. Transfer Learning (CNN) - High accuracy
echo 3. Ensemble (ANFIS + CNN) - Maximum accuracy
echo.
echo Choose your training approach:
echo.
echo [1] ANFIS Training (Recommended for starting)
echo [2] Transfer Learning Training (Best accuracy)
echo [3] Ensemble Training (Maximum accuracy)
echo [4] Install Dependencies First
echo [5] Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto anfis
if "%choice%"=="2" goto transfer
if "%choice%"=="3" goto ensemble
if "%choice%"=="4" goto install
if "%choice%"=="5" goto exit

echo Invalid choice. Please try again.
pause
goto :eof

:install
echo.
echo Installing required packages...
call venv\Scripts\activate.bat
pip install tensorflow scikit-learn opencv-python numpy pandas pillow
echo.
echo Dependencies installed successfully!
echo You can now run any training option.
pause
goto :eof

:anfis
echo.
echo ========================================
echo Starting ANFIS Training
echo ========================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install scikit-learn opencv-python numpy pandas

echo.
echo Starting ANFIS training...
python train_anfis_improved.py

echo.
echo ANFIS Training completed!
echo Expected accuracy: 60-75% with more photos
echo Check the models/ and training_output/ directories for results.
pause
goto :eof

:transfer
echo.
echo ========================================
echo Starting Transfer Learning Training
echo ========================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install tensorflow scikit-learn opencv-python numpy pandas pillow

echo.
echo Starting Transfer Learning training...
echo This will take 30-60 minutes depending on your hardware.
python train_transfer_learning.py

echo.
echo Transfer Learning Training completed!
echo Expected accuracy: 85-95% with current dataset
echo Check the models/ and training_output/ directories for results.
pause
goto :eof

:ensemble
echo.
echo ========================================
echo Starting Ensemble Training
echo ========================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install tensorflow scikit-learn opencv-python numpy pandas pillow

echo.
echo Starting Ensemble training...
echo This will take 45-90 minutes depending on your hardware.
python train_ensemble.py

echo.
echo Ensemble Training completed!
echo Expected accuracy: 90-98% with current dataset
echo Check the models/ and training_output/ directories for results.
pause
goto :eof

:exit
echo.
echo Thank you for using Bell Pepper Hybrid Training System!
echo.
echo To add more photos later:
echo 1. Add photos to the appropriate folders in datasets/Bell Pepper dataset 1/
echo 2. Run the training script again
echo 3. The model will automatically use the new photos
echo.
pause 