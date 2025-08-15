#!/usr/bin/env python3

# -- built-ins
from datetime import datetime, timedelta, timezone
import importlib
from multiprocessing import Process
from sys import argv
import threading

# -- pip-installed
from croniter import croniter

# -- project-libs
from common.utils import config, log, Status, ts

__version__ = '1.3.0'

default_timer = 60  # in second
_g = {'previously_loaded': {}}


def run_job(job_name:str=None, params:dict=None) -> list[Status]:
    """
    Run jobs.
    :param job_name: name of the job to run
    :param params: optional parameters for the job e.g. {job_name: {key: value, ...}}
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
    if not jobs and not params:
        jobs, params = _config_get_list()
    if params and isinstance(params, dict):
        log.debug(f"{fn} : parameters: {params}")
        for k, v in params.items():
            _argv.update({k: (v,)})
            if k not in jobs:
                jobs += [k]
    del params

    # -- run jobs
    for j in jobs:
        module = get_module(j)
        try:
            process = Process(
                target=module.run,
                args=(_argv[j],) if _argv.get(j) else ())
            process.start()
            s.code = 200
            s.message = f'Job "{j}" was successfully launched.'
            statuses += [s.to_dict()]
            log.info(f"{fn} : {s.message}")
        except Exception as e:
            s.code = 500
            s.message = f'Error encountered while running "{j}" -- ' \
                        f'check if exists or the logs. \n{e}'
            statuses += [s.to_dict()]
            log.error(f"{fn} : {s.message}")
        finally:
            del module
    return statuses


def _config_get_list() -> tuple[list, dict]:
    """
    Return runnable jobs for this period.
    :return: list of jobs
    :return: list of parameters for each job
    """
    fn = '[common.scheduler][config_get_list]'
    jobs = []
    params = []

    config.read()
    crons = config['crontab'] if isinstance(config['crontab'], dict) else {}
    for j, t in crons.items():
        v2_plus = True if isinstance(t, dict) else False
        # -- version 1.x.x processing
        if not v2_plus:
            if isexecutable(get_next_event(t), job_name=j):
                jobs += [j]
        # -- version 2.x.x processing
        elif v2_plus and isexecutable(get_next_event(t.get('schedule')), job_name=j):
            jobs += [j]
            params += [{j: t.get('params')}]

    log.debug(f"{fn} : updated list of jobs: {jobs}")
    return jobs, params


def get_module(job_name):
    """
    Try to load module with the run() function.
    """
    fn = '[common.scheduler][get_module]'
    module = None

    if not job_name:
        return module
    try:
        # -- load or reload module
        if job_name in _g['previously_loaded']:
            module = importlib.reload(_g['previously_loaded'][job_name])
            reloaded = True
        else:
            module = importlib.import_module(job_name)
            _g['previously_loaded'][job_name] = module
            reloaded = False

        # -- validate module
        if 'run' not in dir(module):
            del module
            module = None
            log.error(
                f'{fn} : "{job_name}" cannot be executed. '
                f"Make sure there is a run() function in the module.")
        else:
            log.info(
                f'{fn} : module "{job_name}" is now '
                f"{'re-' if reloaded else ''}loaded.")
    except Exception as e:
        log.error(f'{fn} : module "{job_name}" could not be found. Check the path.\n{e}')
    return module


def get_next_event(timer_str, count=1) -> datetime:
    """
    Returns next event time (object)
    :param time_str: cron formatted schedule string (https://en.wikipedia.org/wiki/Cron)
    :return: datetime
    """
    fn = '[common.scheduler][get_next_event]'
    r = []

    def fmt_timer(_base):
        _r = None
        try:
            _r = croniter(timer_str, _base).get_next(datetime)
        except Exception as e:
            log.error(f"{fn} : error found with cron-formatted timer: {timer_str}\n{e}")
        return _r

    base = datetime.now(timezone.utc)-timedelta(seconds=default_timer-1)
    for _ in range(count):
        base = fmt_timer(base)
        r.append(base)
    return r if count > 1 else r[0]


def isexecutable(dt:datetime, job_name:str=None) -> bool:
    """
    Validate event is between [now-default_timer-1]  and [now].
    """
    fn = '[common.scheduler][isexecutable]'
    r = False
    try:
        now = datetime.now(timezone.utc)
        st = now-timedelta(seconds=default_timer-1)
        if dt > st and dt <= now:
            r = True
        log.debug(
            f"{fn} : ? {st} > [{dt}] < {now} {r} "
            f"{'('+job_name+')' if job_name else ''}")
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
