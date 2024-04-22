from common.utils import log, Status


def run(params:dict=None) -> tuple[dict, Status]:
    """
    Running job.
    :param params: list of tuples with key-value pairs. e.g. [('key', 'value'), ...]
    :return: tuple with dictionary and status. e.g. ({'key': 'value'}, Status(200, 'message'))
    """
    fn = '[cron.job_example.run]'
    s = Status(204, f"No data.")

    log.info(f"{fn} running...")

    if params:
        log.debug(f"{fn} : received parameters: {params}")
    res = True

    log.info(f"{fn} done.")
    if res:
        s.code = 200
        s.message = f"job_example ran successfully."
    return s


if __name__ == "__main__":
    run()
