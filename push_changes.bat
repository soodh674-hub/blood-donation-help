@echo off
echo Blood Donation Project - Push Changes Script
echo.
echo This script will help you push your changes to GitHub
echo.
echo IMPORTANT: Before running this script, you need to:
echo 1. Create a Personal Access Token on GitHub
echo 2. Have your token ready to paste when prompted
echo.
echo The changes on branch 'fix-deployment-issues' include:
echo - Fixed login 500 error with improved error handling
echo - Enhanced database and cache configuration for deployment
echo - Fixed URL patterns and imports
echo - Added duplicate directory to .gitignore
echo.
echo Press any key to continue with the push...
pause > nul

git push origin fix-deployment-issues

echo.
echo Push completed! Check the output above for any errors.
echo.
echo If you received authentication errors:
echo 1. Make sure you entered your GitHub username (soodh674-hub) correctly
echo 2. Make sure you used your Personal Access Token (not password) when prompted
echo.
pause