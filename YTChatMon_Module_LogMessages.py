from logger import logger
from YTChatMon_Submodule_ChatReader import chatreader
from YTChatMon_Submodule_Configfile import readconfig, ConfigObject
import argparse
from pathlib import Path

MODULE_FOLDER = Path(__file__).resolve().parent
CONFIG = None
LOG = None
ARGS = None
ALL_CONFIG: ConfigObject
MAIN_CONFIG_FILE = "YTChatMon.toml"

LAST_MESSAGE = 0


def log_message(message):
    global LAST_MESSAGE
    global CONFIG

    #    if message.timestamp > LAST_MESSAGE:
    with open(CONFIG.MESSAGE_LOGFILE, mode="a") as f:
        f.write(f"{message.datetime} {message.timestamp} [{message.author.name}]- {message.message}\n")


#            LAST_MESSAGE = message.timestamp


def main():
    global CONFIG
    global LOG
    global ARGS
    global ALL_CONFIG
    print(f"Loading config from {MAIN_CONFIG_FILE}")
    ALL_CONFIG = readconfig(MAIN_CONFIG_FILE)
    CONFIG = ALL_CONFIG.LogMessages

    print(f"Module_LogMessages - Logging event to {CONFIG.EVENTLOG}")
    LOG = logger.get_logger(__file__, logger.DEBUG, CONFIG.EVENTLOG)

    parser = argparse.ArgumentParser(
        prog=f"{__file__}", description="LogMessage for youtube", epilog="a mbeware monstruosity"
    )
    parser.add_argument("--streamid", help="Start monitoring the live stream")
    ARGS = parser.parse_args()

    if not ARGS.streamid:
        if "STREAMID" in ALL_CONFIG["GLOBAL"].keys():
            LOG.info(f"Starting with streamid from config file : {ALL_CONFIG['GLOBAL']['STREAMID']}")
            ARGS.streamid = str(ALL_CONFIG["GLOBAL"]["STREAMID"])
        else:
            ARGS.streamid = "PCOOSewAYMc"  # for testing.
            LOG.info(f"Starting with hardcoded streamid {ARGS.streamid}")
    else:
        LOG.info(f"Starting with commandline streamid : {ARGS.streamid}")
    print("Module_LogMessages - Ready. Waiting for messages")
    chatreader(log_message, ARGS.streamid, "LogMessages")


if __name__ == "__main__":
    print(f"Module_LogMessages - Version : {Path('version.txt').read_text()}")
    main()
