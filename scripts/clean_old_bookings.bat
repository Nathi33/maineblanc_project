@echo off
REM Activate your virtual environment
call C:\Users\natha\camping_site\venv\Scripts\activate.bat

REM Navigate to the Django project directory
cd C:\Users\natha\camping_site\maineblanc_project

REM Run the Django command
python manage.py clean_old_bookings
python manage.py clean_old_bookings --anonymize

REM Quit the virtual environment
deactivate
