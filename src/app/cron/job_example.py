from common.utils import log, Status


def run(params:dict=None) -> str:
    """
    Running job.
    :param params: list of tuples with key-value pairs as JSON.
                   e.g. [{"<key>": "<value>", "<key>": "<value>"}]
    :return: Status(<200>, '<message>') json string
    """
    fn = '[cron.job_example][run]'
    s = Status(204, f"No data.")

    log.info(f"{fn} running...")

    if params:
        log.debug(f"{fn} : received parameters: {params}")
    res = True

    log.info(f"{fn} done.")
    if res:
        s.code = 200
        s.message = f"job_example ran successfully."
    return s.to_str()


if __name__ == "__main__":
    run()
