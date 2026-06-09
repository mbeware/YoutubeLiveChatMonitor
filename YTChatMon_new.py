import subprocess
from pathlib import Path
from logger import logger, colors
from YTChatMon_Submodule_Configfile import readconfig, ConfigObject
import argparse


MODULE_FOLDER = Path(__file__).resolve().parent
CONFIG = None
LOG: logger.Logger
ARGS = None
ALL_CONFIG: ConfigObject
MAIN_CONFIG_FILE = "YTChatMon.toml"


def start_all_modules(streamid):
    # todo - check if keys are in config
    # todo - check if executable exists
    # todo - check if exit_codes are OK

    try:
        module_list = ALL_CONFIG["MODULES"]["MODULE_LIST"]
        LOG.debug(f"{module_list=}")
        processes = []
        for module in module_list:
            executable = ALL_CONFIG[module]["EXECUTABLE"]
            LOG.info(f"Starting module {module} with the executable {executable}")
            processes.append(subprocess.Popen(["/usr/bin/env", "python3", executable, "--streamid", streamid]))

        # Wait for all to finish
        exit_codes = [current_process.wait() for current_process in processes]
        LOG.info(f"{exit_codes=}")
    except KeyboardInterrupt:
        print(
            f'{colors.OKBLUE}** CTRL-C - you are breaking up with me? fine, just kill me then. What do you mean by {colors.BOLD}"that is what is going to ha{colors.ENDC}{colors.OKBLUE}/{colors.FAIL}PROCESS TERMINATED{colors.OKGREEN} ;-){colors.ENDC}'
        )
    except Exception as e:
        LOG.critical(f"start_all_modules - exception : {e}")
        print(f"YTChatMon - start_all_modules - exception : {e}")

    finally:
        for current_process in processes: # type: ignore
            if current_process.poll() is None:
                current_process.kill()


def main():
    global CONFIG
    global LOG
    global ARGS
    global ALL_CONFIG
    print(f"YTChatMon - Loading config from {MAIN_CONFIG_FILE}")
    ALL_CONFIG = readconfig(MAIN_CONFIG_FILE)
    CONFIG = ALL_CONFIG.YTChatMon

    print(f"YTChatMon - Logging event to {CONFIG.EVENTLOG}")
    LOG = logger.get_logger(__file__, logger.DEBUG, CONFIG.EVENTLOG)

    parser = argparse.ArgumentParser(
        prog=f"{__file__}", description="Chat monitor for youtube", epilog="a mbeware monstruosity"
    )
    parser.add_argument("--streamid", help="Start monitoring the live stream")
    ARGS = parser.parse_args()

    if not ARGS.streamid:
        if "STREAMID" in ALL_CONFIG["GLOBAL"].keys():
            LOG.info(f"Starting with streamid from config file : {ALL_CONFIG['GLOBAL']['STREAMID']}")
            print(f"YTChatMon - Starting with streamid from config file : {ALL_CONFIG['GLOBAL']['STREAMID']}")
            ARGS.streamid = str(ALL_CONFIG["GLOBAL"]["STREAMID"])
        else:
            ARGS.streamid = "PCOOSewAYMc"  # for testing.
            LOG.info(f"Starting with hardcoded streamid {ARGS.streamid}")
            print(f"YTChatMon - Starting with hardcoded streamid : {ARGS.streamid}")
    else:
        LOG.info(f"Starting with commandline streamid : {ARGS.streamid}")
        print(f"YTChatMon - Starting with commandline streamid : {ARGS.streamid}")

    start_all_modules(ARGS.streamid)


if __name__ == "__main__":
    print(f"YTChatMon - Version : {Path('version.txt').read_text()}")
    main()
