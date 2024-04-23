#!/usr/bin/env python3

# -- built-ins
from datetime import datetime, timedelta
import importlib
import json
from multiprocessing import Process
from sys import argv
import threading

# -- pip-installed
from croniter import croniter

# -- project-libs
from common.utils import config, log, Status

__version__ = '1.1.0'

default_timer = 60  # in second


def run_job(job_name:str=None, params:dict=None) -> list[Status]:
    """
    Run jobs.
    :param job_name: name of the job to run
    :param params: optional parameters for the job e.g. {key: value, ...}
    """
    fn = '[common.scheduler][run_job]'
    s = Status(204, f"No job ran.")
    statuses = []
    jobs = []
    _argv = {}

    log.info(f'{fn} : launching {job_name if job_name else "jobs"}...')

    # -- validate parameters
    if isinstance(job_name, str):
        jobs = [job_name]
    if not jobs:
        jobs, params = get_list()
    if params and isinstance(params, dict):
        log.debug(f"{fn} : parameters: {params}")
        for k, v in params.items():
            _argv.update({k: (v,)})
        del params

    # -- run jobs
    for j in jobs:
        module = get_mod(j)
        try:
            process = Process(
                target=module.run,
                args=(json.dumps(_argv[j]),) if _argv.get(j) else None)
            process.start()
            s.code = 200
            s.message = f'{fn} : Job "{j}" was successfully launched.'
            statuses += [s]
            log.info(f"{fn} : {s.message}")
        except Exception as e:
            s.code = 500
            s.message = f'{fn} : Error encountered while running "{j}" -- ' \
                        f'check if exists or the logs. \n{e}'
            statuses += [s]
            log.error(f"{s.message}")
        finally:
            del module
    return statuses


def get_list() -> tuple[list, dict]:
    """
    Return runnable jobs for this period.
    :return: list of jobs
    :return: list of parameters for each job
    """
    jobs = []
    params = []

    config.read()
    crons = config['crontab']  # if config['crontab'] else []
    for j, t in crons.items():
        v2_plus = True if isinstance(t, dict) else False
        # -- version 1.x.x processing
        if not v2_plus:
            if isexecutable(get_next_event(t)):
                jobs += [j]
        # -- version 2.x.x processing
        elif v2_plus and isexecutable(get_next_event(t.get('schedule'))):
            jobs += [j]
            params += [{j: t.get('params')}]

    log.debug(f"updated list of jobs: {jobs}")
    return jobs, params


def get_mod(job_name):
    """
    Try to load module with the run() function.
    """
    fn = '[common.scheduler][get_mod]'
    r = None

    if not job_name:
        return r
    try:
        r = importlib.import_module(job_name)
        if 'run' not in dir(r):
            del r
            r = None
            log.error(
                f'{fn} : "{job_name}" cannot be executed. '
                f"Make sure there is a run() function in the module.")
        else:
            log.debug(f'module "{job_name}" is now loaded.')
    except Exception as e:
        log.error(
            f'{fn} : module "{job_name}" could not be found. Check the path.'
            f"\n{e}")
    return r


def get_next_event(timer_str) -> datetime:
    """
    Returns next event time (object)
    :param time_str: cron formatted schedule string (https://en.wikipedia.org/wiki/Cron)
    :return: datetime
    """
    fn = '[common.scheduler][get_next_event]'
    r = None
    try:
        base = datetime.utcnow()-timedelta(seconds=default_timer-1)
        r = croniter(timer_str, base).get_next(datetime)
    except Exception as e:
        log.error(
            f"{fn} : error found with cron-formatted timer: {timer_str}\n{e}")
    return r


def isexecutable(dt:datetime):
    """
    Validate event is between [now-default_timer-1]  and [now].
    """
    fn = '[common.scheduler][isexecutable]'
    r = False
    try:
        now = datetime.utcnow()
        st = now-timedelta(seconds=default_timer-1)
        if dt > st and dt <= now:
            r = True
        log.debug(f"{fn} : ? [{st}] > [{dt}] < [{now}]")
    except:
        pass
    return r


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
            '  -n        refresh rate interval in seconds\n')
        exit()
    wakeup()
