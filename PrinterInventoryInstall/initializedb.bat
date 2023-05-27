set root_password=
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p"%root_password%" < %~dp0\..\build_printers_db.sql