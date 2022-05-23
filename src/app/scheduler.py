#!/usr/bin/env python3

# -- built-ins
from datetime import datetime, timedelta
import importlib
import multiprocessing
from sys import argv
import threading

# -- pip-installed
from croniter import croniter

# -- project-libs
from auto_utils import config, log

__version__ = '1.0.1'

default_timer = 60  # in second


def get_next_event(timer_str) -> datetime:
    """
    Returns next event time (object)
    :param time_str: cron formatted schedule string (https://en.wikipedia.org/wiki/Cron)
    :return: datetime
    """
    r = None
    try:
        base = datetime.utcnow()-timedelta(seconds=default_timer-1)
        r = croniter(timer_str, base).get_next(datetime)
    except Exception as e:
        log.error(f"error found with cron-formatted timer: {timer_str}\n{e}")
    return r


def get_mod(job_name):
    """
    Try to load module with the run() function.
    """
    r = None

    if not job_name:
        return r
    try:
        r = importlib.import_module(job_name)
        if 'run' not in dir(r):
            del r
            r = None
            log.error(
                f"{job_name} cannot be executed. "
                f"Make sure there is a run() function in the module.")
        else:
            log.debug(f"module {job_name} is now loaded.")
    except:
        log.error(f"module {job_name} could not be found. Check the path.")
    return r


def get_list():
    """
    Return runnable jobs for this period.
    """
    r = []
    config.read()
    crons = config['crontab']
    if crons:
        for j, t in crons.items():
            if isexecutable(get_next_event(t)):
                r += [j]
    log.debug(f"updated list of jobs: {r}")
    return r


def isexecutable(dt: datetime):
    """
    Validate event is between [now-default_timer-1]  and [now].
    """
    r = False
    try:
        now = datetime.utcnow()
        st = now-timedelta(seconds=default_timer-1)
        if dt > st and dt <= now:
            r = True
        log.debug(f"? [{st}] > [{dt}] < [{now}]")
    except:
        pass
    return r


def run_job(job_name: str=None) -> None:
    """
    Run jobs.
    """
    jobs = []

    if job_name:
        jobs = [job_name]
    if not jobs:
        jobs = get_list()

    for j in jobs:
        module = get_mod(j)
        try:
            log.info(f"scheduler: running jobs... [{j}][{config['crontab'][j]}]")
            process = multiprocessing.Process(target=module.run)
            process.start()
        except:
            log.error(f"issues encountered while running {j}.")
        finally:
            del module


def wakeup() -> None:
    """
    Event-loop to run jobs based on their schedule.
    """
    # -- get updated job list and run all jobs as of now()
    run_job()

    # -- time-bomb!
    threading.Timer(default_timer, wakeup).start()


if __name__ == "__main__":
    if '-n' in argv:
        try:
            default_timer = int(argv[argv.index('-n')+1])
        except:
            log.error(f"scheduler(): -n argument is missing a value. (default: {default_timer})")
    if '--help' in argv:
        print(
            '\nUsage: ./scheduler.py [OPTION] \n'
            '  -n        refresh rate interval in seconds\n'
        )
        exit()
    wakeup()
