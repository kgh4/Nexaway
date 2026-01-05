@echo off
mkdir .playwright\node_modules\playwright\browsers\chromium-1200 2>nul
powershell -Command "Invoke-WebRequest -Uri 'https://playwright.download.prss.microsoft.com/dbazure/download/playwright/builds/chromium/1200/chromium-win64.zip' -OutFile chromium.zip"
powershell -Command "Expand-Archive chromium.zip -DestinationPath .playwright\node_modules\playwright\browsers\chromium-1200"
powershell -Command "Move-Item .playwright\node_modules\playwright\browsers\chromium-1200\chrome-headless-shell-win64\* .playwright\node_modules\playwright\browsers\chromium-1200 -Force"
rm chromium.zip
echo ✅ Playwright Chromium installed manually!
echo Run: python run.py
