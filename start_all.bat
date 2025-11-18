@echo off
echo 🚀 Starting PTPanel Services from run_files...

echo 🤖 Starting Admin Bot...
start python run_files/run_adminbot.py

echo 🤖 Starting WebApp Bot...
start python run_files/run_webapp_bot.py

echo 🤖 Starting Classic Bot...
start python run_files/run_classic_bot.py

echo 🤖 Starting Multitool Bot...
start python run_files/run_multitool_bot.py

echo 🌐 Starting Flask Server...
start python run.py

echo ✅ All services started!
echo 📊 Admin Panel: http://localhost:5000/admin
echo 📝 Check logs in logs/ folder
pause