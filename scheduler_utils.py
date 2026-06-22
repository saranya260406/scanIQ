import time
import schedule

def start_scheduler(settings, job_function):

    scan_time = settings.get_scan_time()

    print("\n[SCHEDULER] Started")
    print(f"[SCHEDULER] Daily scan time: {scan_time}")

    schedule.every().day.at(scan_time).do(job_function)

    while True:
        schedule.run_pending()
        time.sleep(30)