@echo off
echo === Cai dat thu vien ===
pip install django==5.2.13 pillow==12.2.0
echo.
echo === Khoi dong server ===
python manage.py runserver
pause
