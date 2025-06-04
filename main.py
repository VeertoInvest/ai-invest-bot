import threading
import schedule
import time
from keep_alive import keep_alive

def job():
    print("✅ Bot running scheduled task... (заглушка)")

schedule.every(4).hours.do(job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    keep_alive()  # запуск HTTP-сервера
    threading.Thread(target=run_scheduler).start()
    print("✅ Bot started and keep_alive active.")
