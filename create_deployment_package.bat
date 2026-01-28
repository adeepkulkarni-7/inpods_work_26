@echo off
echo ================================================
echo   Creating Deployment Package
echo ================================================
echo.

REM Create deployment folder
if exist "deployment_package" rmdir /s /q "deployment_package"
mkdir "deployment_package"

REM Copy backend files
echo Copying backend files...
mkdir "deployment_package\backend_v2"
copy "backend_v2\app.py" "deployment_package\backend_v2\"
copy "backend_v2\audit_engine.py" "deployment_package\backend_v2\"
copy "backend_v2\visualization_engine.py" "deployment_package\backend_v2\"
copy "backend_v2\requirements.txt" "deployment_package\backend_v2\"
copy "backend_v2\.env.example" "deployment_package\backend_v2\"

REM Copy frontend files
echo Copying frontend files...
mkdir "deployment_package\frontend_v2"
copy "frontend_v2\index.html" "deployment_package\frontend_v2\"

REM Copy startup scripts
echo Copying startup scripts...
copy "run_v2.bat" "deployment_package\"
copy "run_v2.sh" "deployment_package\"

REM Copy documentation
echo Copying documentation...
copy "DEPLOYMENT_GUIDE.md" "deployment_package\"
copy "TECHNICAL_DOCUMENTATION_V2.md" "deployment_package\"

REM Create empty folders
mkdir "deployment_package\backend_v2\uploads"
mkdir "deployment_package\backend_v2\outputs"
mkdir "deployment_package\backend_v2\outputs\insights"
mkdir "deployment_package\backend_v2\outputs\library"

echo.
echo ================================================
echo   Deployment Package Created!
echo.
echo   Location: deployment_package\
echo.
echo   Next steps:
echo   1. ZIP the deployment_package folder
echo   2. Send to other machine
echo   3. Unzip and follow DEPLOYMENT_GUIDE.md
echo ================================================
echo.
pause
