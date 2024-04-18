from common.utils import log, Status

def run(params:list[tuple]=None) -> tuple[dict, Status]:
    """
    Running job.
    :param params: list of tuples with key-value pairs. e.g. [('key', 'value'), ...]
    :return: tuple with dictionary and status. e.g. ({'key': 'value'}, Status(200, 'message'))
    """
    fn = '[job_example.run]'
    s = Status(204, f"No data.")

    log.info(f"{fn} running...")

    if params:
        log.debug(f"{fn} : received parameters: {params}")

    log.info(f"{fn} done.")
    s.code = 200
    s.message = f"job_example ran successfully."
    return s