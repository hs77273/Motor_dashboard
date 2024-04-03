@echo off
REM Get the IP address dynamically
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4 Address"') do (
    set "IP_ADDRESS=%%a"
)

REM Trim leading and trailing spaces
set IP_ADDRESS=%IP_ADDRESS: =%
set IP_ADDRESS=%IP_ADDRESS: =%

REM Open URL with dynamically obtained IP address
start http://%IP_ADDRESS%:5000/