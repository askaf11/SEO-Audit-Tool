@echo off
:: Activate the virtual environment
call venv\Scripts\activate

:: Run the Python script in a new command window
start cmd /k python app.py

:: Wait for a few seconds to ensure the server is up
timeout /t 5 /nobreak

:: Print a message to the command prompt
echo Server started. You can now perform the SEO audit. Open your browser and visit http://localhost:5000.

:: Open the local server address in the default browser
start http://localhost:5000

:: Pause to keep the command prompt open
pause
