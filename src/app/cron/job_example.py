from common.utils import log, Status


def run(params:list[tuple]=None) -> str:
    """
    Running job.
    :param params: list of tuples with key-value pairs.
    :return: Status(<200>, '<message>') json string
    """
    fn = '[cron.job_example][run]'
    s = Status(204, f"No data.")
    _argv = {}

    log.info(f"{fn} running...")

    # -- unpack parameters
    _argv = param_unpack(params)

    # -- do something
    res = True

    # -- done
    log.info(f"{fn} done.")
    if res:
        s.code = 200
        s.message = f"job_example ran successfully."
    r = s.to_str()
    log.debug(f"{fn} : return values: {r}")
    return r


def param_unpack(params):
    """
    Parameter unpacking routine
    :param params: list of tuples with key-value pairs.
                e.g. ({"<key>": "<value>", "<key>": "<value>"})
    :return:
    """
    fn = '[cron.job_example][param_unpack]'
    r = {}
    log.debug(f"{fn} : received parameters: {params}, type: {type(params)}")
    if isinstance(params, tuple):
        for param in params:
            for k, v in param.items():
                r[k] = v
        log.debug(f"{fn} : params unpacked: {r}")
    return r


if __name__ == "__main__":
    run()
