from logger import logger
from pathlib import Path
import pytchat
from typing import Callable


import pytchat
import time


def chatreader(message_handler: Callable, streamid):

    chat = pytchat.create(video_id=streamid)

    while chat.is_alive():
        chatdata = chat.get()
        if chatdata:
            items = chatdata.items

            for message in items:
                message_handler(message)

    try:
        chat.raise_for_status()
    except pytchat.ChatdataFinished:
        print("chat data finished")
    except Exception as e:
        print(type(e), str(e))


def chatreader_old(message_handler: Callable, streamid):
    chat = pytchat.LiveChat(video_id=streamid)
    a = chat.is_alive()
    while a:
        try:
            data = chat.get()
            if data:
                items = data.items

                for message in items:
                    message_handler(message)

        except KeyboardInterrupt:
            chat.terminate()
            print("keyboard interrupt")
            break

        except Exception as e:
            print(f"{e} exception (reader)")
        a = chat.is_alive()

    print(f"{chat.is_alive()=}")
    print(f"{a=}")


LOG = logger.get_logger(__file__, logger.DEBUG, f"{Path(__file__).stem}.log")
LOG.info(f"{__name__} loaded as module")
