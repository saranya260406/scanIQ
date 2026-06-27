import time
import schedule
import threading
import logging

logger = logging.getLogger(__name__)


def start_scheduler(settings, job_function, stop_event=None):
    """
    Start the scheduler in a separate thread.
    The job_function will only run at the scheduled time.
    
    Args:
        settings: Settings object with get_scan_time() method
        job_function: Function to call at scheduled time
        stop_event: threading.Event to signal scheduler to stop (optional)
    
    Returns:
        threading.Thread: The scheduler thread
    """
    scan_time = settings.get_scan_time()
    
    logger.info(f"[SCHEDULER] Starting scheduler - Daily CSV export time: {scan_time}")
    
    # Schedule the job only at specified time, never on startup
    schedule.every().day.at(scan_time).do(job_function)
    
    def scheduler_loop():
        logger.info("[SCHEDULER] Scheduler thread running")
        while True:
            schedule.run_pending()
            
            # Check if stop event is set (with timeout to allow graceful shutdown)
            if stop_event and stop_event.wait(timeout=30):
                logger.info("[SCHEDULER] Scheduler stopping")
                break
            
            if not stop_event:
                time.sleep(30)
    
    # Create and start scheduler thread as daemon
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True, name="SchedulerThread")
    scheduler_thread.start()
    
    logger.info(f"[SCHEDULER] CSV will be exported daily at {scan_time}")
    
    return scheduler_thread