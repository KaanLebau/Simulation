
import datetime
import os
import sys


SIMULATION_START = datetime.datetime(2025, 4, 11, 4,0)



# LOG file directories
LOG_DIR = "./logs/6mounts"
os.makedirs(LOG_DIR, exist_ok=True)
EVENTS_PATH = os.path.join(LOG_DIR, "event.csv")
LOG_PATH = os.path.join(LOG_DIR,'line_log.csv')
RESULTS_PATH = os.path.join(LOG_DIR, "results.txt")
