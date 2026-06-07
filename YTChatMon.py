# Todo
############
# [X] Reader
# [X] Dispatcher
## [X] DynamicModules
## [ ] REplacie with https://pypi.org/project/pluginbase/
## [ ] Mod:Logguer
## [ ] Mod:Commander
### [ ] Admin commands
### [ ] SuperMod commands
### [ ] Moderator commands
### [ ] User commands
## [ ] Mod:Text2Voice

## [ ] change all     logger.debug(f"Entered {sys._getframe().f_code.co_name}") for a decorator.

from YTChatMon_loadmodules import load_modules_from_config


#


import argparse
from pathlib import Path
import pytchat
import asyncio  # Less issue with asyncio, but less effective
import inspect
import tomllib
import sys
import logging


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File Handler (All levels)
file_handler = logging.FileHandler("YTChatMon.log")
file_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Attach handlers
logger.addHandler(file_handler)

logger.debug("Started YTChatBot")


async def reader(context):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    chat_queue = context["chat_queue"]
    YoutubeLiveStreamID = context["args"].streamid

    chat = pytchat.create(video_id=YoutubeLiveStreamID)
    try:
        while chat.is_alive():
            for c in chat.get().sync_items():  # type: ignore
                await chat_queue.put(c)
            await asyncio.sleep(0.5)
        logger.debug("stream chat is not alive anymore")

    except asyncio.CancelledError:
        logger.debug(f"Exception CancelledError {sys._getframe().f_code.co_name}")

    except Exception as e:
        logger.debug(f"Exception {e} {sys._getframe().f_code.co_name}")
        print(f"{e} exception (reader)")

    finally:
        await chat_queue.put(None)
        logger.debug(f"Exited {sys._getframe().f_code.co_name}")


async def dispatcher(context):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    chat_queue = context["chat_queue"]
    modules = context["modules"]

    try:
        while True:
            message = await chat_queue.get()  # Blocking/wait forever

            if message is None:
                logger.debug("message is None. Signal to end everything")
                break

            tasks = []
            for name, module in modules.items():
                if hasattr(module, "process_message"):
                    func = module.process_message

                    if inspect.iscoroutinefunction(func):
                        tasks.append(func(message, context))
                    else:
                        # wrap sync in thread to avoid blocking
                        loop = asyncio.get_running_loop()
                        tasks.append(loop.run_in_executor(None, func, message, context))
            if len(tasks) > 0:
                await asyncio.gather(*tasks, return_exceptions=True)

            sys.stdout.write(f"\rMessages left in queue : {chat_queue.qsize()}")
            sys.stdout.flush()

    except asyncio.CancelledError:
        logger.debug(f"Exception CancelledError {sys._getframe().f_code.co_name}")
        # pass  # We have been cancelled. What did we do????

    # we should send a message to reader to tell it that we dont dispatch anymore...


async def get_modules_configs(context):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    modules = context["modules"]

    try:
        tasks = []
        for name, module in modules.items():
            if hasattr(module, "add_config_to_context"):
                func = module.add_config_to_context

                if inspect.iscoroutinefunction(func):
                    tasks.append(func(context))
                else:
                    # wrap sync in thread to avoid blocking
                    loop = asyncio.get_running_loop()
                    tasks.append(loop.run_in_executor(None, func, context))
        if len(tasks) > 0:
            await asyncio.gather(*tasks, return_exceptions=True)

    except asyncio.CancelledError:
        pass  # We have been cancelled. What did we do????
    logger.debug(f"Exitged {sys._getframe().f_code.co_name}")
    # we should send a message to reader to tell it that we dont dispatch anymore...


async def start_monitor(context):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    # Reader will put messages in a queue
    # Dispatcher will read from queue and invoque appropriate module

    await get_modules_configs(context)

    # create queue
    chat_queue = asyncio.Queue(0)
    context["chat_queue"] = chat_queue
    reader_t = asyncio.create_task(reader(context))
    dispatcher_t = asyncio.create_task(dispatcher(context))

    try:
        print(f"{__file__} succesffuly started... Probably... Maybe...")
        await asyncio.gather(dispatcher_t, reader_t)

    except KeyboardInterrupt:
        reader_t.cancel()
        dispatcher_t.cancel()
        await asyncio.gather(dispatcher_t, reader_t, return_exceptions=True)
        logger.debug(f"keyboard interrupt {sys._getframe().f_code.co_name}")
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")


# def create_config():
#     print("create_config doesnt work anymore")
#     return

#     config_path = Path.home() / ".config" / "YoutubeLiveChatMonitor"
#     config_file = config_path / "config.toml"

#     # Creates all intermediate directories if they don't exist
#     os.makedirs(config_path , exist_ok=True)

#     if config_file.exists():
#         raise FileExistsError(f"Config file already exists: {config_path}")


#     # Create a new TOML document
#     config = tomlkit.document()
#     config_general = tomlkit.table()
#     config_general["modules_list"] = ["printmsg","TTS"]
#     config_printmsg = tomlkit.table()
#     config_printmsg.add(('file_path = "printmsg/printmsg.py"'))
#     config_tts = tomlkit.table()
#     config_tts.add(('file_path = "ttsbot/ttsbot.py"'))

#     config.add("general",config_general)
#     config.add("printmsg",config_printmsg)
#     config.add("ttsbot",config_tts)

#     # Write to file
#     with open(config_file, "w") as toml_file:
#         toml_file.write(tomlkit.dumps(config))


def readconfig():
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    # read system.config
    script_dir = Path(__file__).resolve().parent

    config_path = script_dir / "system.config.toml"

    if not config_path.exists():
        raise FileNotFoundError(f"No config file: {config_path}")

    with config_path.open("rb") as f:
        config = tomllib.load(f)
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")
    return config

    ##############################################################
    # No user.config for now.

    # #read user.config
    # config_path = Path.home() / ".config" / "YoutubeLiveChatMonitor" / "user.config.toml"

    # if not config_path.exists():
    #     raise FileNotFoundError(f"No config file: {config_path}")

    # with config_path.open("rb") as f:
    #     config = tomllib.load(f)
    #     return config


def main():
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")

    parser = argparse.ArgumentParser(
        prog="YTChatMon", description="Monitor and act on live youtube chat", epilog="a mbeware monstruosity"
    )

    # parser.add_argument('--install',action='store_true',help='Create configuration files')
    parser.add_argument("--streamid", help="Start monitoring the live stream")
    parser.add_argument("--debug", help=argparse.SUPPRESS)

    args = parser.parse_args()

    # install doesnt work at the moment.
    # if args.install:
    #    create_config()
    #    return 0

    context = {}
    context["args"] = args
    context["config"] = readconfig()

    context["modules"] = load_modules_from_config(context)

    if not args.streamid:
        args.streamid = "anQ1ROeUctk"  # for testing.

    asyncio.run(start_monitor(context))
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")
    return 0


if __name__ == "__main__":
    print(f"Version : {Path('version.txt').read_text()}")
    exit(main())
else:
    print("{__name__} loaded as module")
