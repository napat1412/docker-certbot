import schedule
import time

print("start application")

def job():
    print("I'm working... ")

schedule.every(1).minutes.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
