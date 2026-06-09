from logger import logger, colors
from pathlib import Path
import pytchat
from typing import Callable
from YTChatMon_Submodule_Configfile import readconfig, ConfigObject

MODULE_FOLDER = Path(__file__).resolve().parent
CONFIG = None
LOG: logger.Logger
ARGS = None
ALL_CONFIG: ConfigObject
MAIN_CONFIG_FILE = "YTChatMon.toml"


def start_logger(caller_module_name):
    global CONFIG
    global LOG
    global ARGS
    global ALL_CONFIG
    print(f"Loading config from {MAIN_CONFIG_FILE}")
    ALL_CONFIG = readconfig(MAIN_CONFIG_FILE)
    CONFIG = ALL_CONFIG.ChatReader

    print(f"SubModule_ChatReader ({caller_module_name}) - Logging event to {caller_module_name}.{CONFIG.EVENTLOG}")
    LOG = logger.get_logger(__file__, logger.DEBUG, f"{caller_module_name}.{CONFIG.EVENTLOG}")


def chatreader2(message_handler: Callable, streamid, caller_module_name):
    global LOG
    print(f"SubModule_CHatReader - chatreader for ({caller_module_name}) started")
    start_logger(caller_module_name)
    chat = pytchat.create(video_id=streamid)
    ots = 0
    while chat.is_alive():
        chatdata = chat.get()
        if chatdata:
            items = chatdata.items  # type: ignore

            for message in items:
                if message.timestamp > ots:
                    message_handler(message)
                    ots = message.timestamp

    try:
        chat.raise_for_status()
    except pytchat.ChatdataFinished as e: # type: ignore
        LOG.info("chatreader2 - chat data finished")
        LOG.critical(f"SubModule_ChatReader - {type(e)}, {str(e)}")
        print(f"{colors.WARNING}** Error - Send this and all the logs to mbeware ****************{colors.ENDC}")
        print(f"SubModule_ChatReader - {type(e)}, {str(e)}")
        print(f"{colors.WARNING}*****************************************************************{colors.ENDC}")
        return


def chatreader(message_handler: Callable, streamid, caller_module_name):
    m = f"{colors.WARNING}chatreader - escapted chatreader2, but recaptured in chatreader. sending execution back to charreader2{colors.ENDC}"
    while True:
        try:
            chatreader2(message_handler=message_handler, streamid=streamid, caller_module_name=caller_module_name)
            LOG.debug(m)
            print(f"{colors.WARNING}** Error - Send this and all the logs to mbeware ****************{colors.ENDC}")
            print(m)
            print(f"{colors.WARNING}*****************************************************************{colors.ENDC}")

        except KeyboardInterrupt:
            print(
                f'{colors.OKBLUE}** CTRL-C - you are breaking up with me? fine, just kill me then. What do you mean by {colors.BOLD}"that is what is going to ha{colors.ENDC}{colors.OKBLUE}/{colors.FAIL}PROCESS TERMINATED{colors.OKGREEN} ;-){colors.ENDC}'
            )
            break
        except Exception as e:
            LOG.critical(f"SubModule_ChatReader - {type(e)}, {str(e)}")
            print(f"{colors.WARNING}** Error - Send this and all the logs to mbeware ****************{colors.ENDC}")
            print(f"SubModule_ChatReader - {type(e)}, {str(e)}")
            print(f"{colors.WARNING}*****************************************************************{colors.ENDC}")
