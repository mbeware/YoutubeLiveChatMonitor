from logger import logger
from YTChatMon_Submodule_ChatReader import chatreader
from YTChatMon_Submodule_Configfile import readconfig, ConfigObject


import argparse
from pathlib import Path


import asyncio
import edge_tts
from dataclasses import dataclass, asdict
import time
import tomlkit
import os
import logging
from datetime import datetime
import subprocess


@dataclass
class User_Info:
    name: str
    TTSname: str
    voice: str
    rate: str
    pitch: str
    volume: str


MODULE_FOLDER = Path(__file__).resolve().parent
MESSAGE = ""
USERS: dict[str, User_Info] = {}
USER_PRESENTATION: dict[str, bytes] = {}
ALLVOICES: list[str] = []
ALLVOICES_CACHE: list[str] = []
LASTUSER = ""
LASTTIME = 0
CONFIG = None
LOG = None
ARGS = None
GAP_START_INFO = ""
GAP_START_TIME = datetime.now()
LOG_TIMING = None
ALL_CONFIG: ConfigObject
MAIN_CONFIG_FILE = "YTChatMon.toml"


def activate_gap():
    global LOG_TIMING
    LOG_TIMING = logger.get_logger("TIMING", logging.DEBUG, CONFIG.GAP_LOG)


def gap_start(info):
    global GAP_START_TIME
    global GAP_START_INFO
    GAP_START_TIME = datetime.now()
    GAP_START_INFO = info


def gap_end(info):
    global GAP_START_TIME
    global GAP_START_INFO
    global LOG_TIMING
    if CONFIG.GAP_MONITOR == "Enabled":
        LOG_TIMING.info(f"{GAP_START_INFO}->{info}:{datetime.now() - GAP_START_TIME}")


def load_voicenames():
    global ALLVOICES
    global ALLVOICES_CACHE

    if len(ALLVOICES_CACHE) > 0:
        ALLVOICES = ALLVOICES_CACHE.copy()
        return

    voicesfile = MODULE_FOLDER / CONFIG.ENGLISH_VOICE_LIST  # remember, MODULE_FOLDER type is a Path, not a string.
    # voicesfile = Path(CONFIG.ENGLISH_VOICE_LIST) # this is what we have to do, when we dont already have a Path type.

    allvoices_raw = voicesfile.read_text().splitlines()
    ALLVOICES = []
    for v in allvoices_raw:
        ALLVOICES.append(v.strip())

    # cache a copy
    ALLVOICES_CACHE = ALLVOICES.copy()


def generate_audio(TTStext="", TTSvoice="", TTSpitch="+0Hz", TTSrate="+0%", TTSvolume="+0%"):
    async def generate_audio_async():
        communicate = edge_tts.Communicate(text=TTStext, voice=TTSvoice, pitch=TTSpitch, rate=TTSrate, volume=TTSvolume)
        audio = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]  # type: ignore

        return audio

    # Run async internally but expose sync API
    return asyncio.run(generate_audio_async())


def generate_and_play_audio(TTStext, TTSvoice="", TTSpitch="+0Hz", TTSrate="+0%", TTSvolume="+0%", presentation=None):
    if not TTStext.strip():
        return

    async def play_audio_async():

        gap_start("Start ffplay")
        process = await asyncio.create_subprocess_exec(
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel",
            "quiet",
            "-i",
            "pipe:0",  # read from stdin
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        gap_end("ffplay started")
        if presentation:
            gap_start("playing presentation")
            process.stdin.write(presentation)
            gap_end("presentation played")
            gap_start("Waiting for buffer")
            await process.stdin.drain()
            gap_end("buffer empty")
        gap_start("Calling TTS")
        communicate = edge_tts.Communicate(text=TTStext, voice=TTSvoice, rate=TTSrate, pitch=TTSpitch, volume=TTSvolume)
        gap_end("TTS called")
        try:
            gap_start("Getting chunks")
            async for chunk in communicate.stream():
                gap_end("Chunk obtained")
                if chunk["type"] == "audio":
                    gap_start("writting to player")
                    process.stdin.write(chunk["data"])
                    gap_end("return from player")
                    gap_start("waiting for buffer")
                    await process.stdin.drain()
                    gap_end("Buffer empty")
                    gap_start("Looping back for next chunk")
        except Exception:
            pass
        finally:
            gap_end("Loop ended")
            gap_start("Closing stdin")
            process.stdin.close()
            gap_end("Stdin closed")
            gap_start("ending process")
            await process.wait()
            gap_end("process ended")

    gap_end("reday to play")
    gap_start("calling async play")
    asyncio.run(play_audio_async())
    gap_end("back from playing async")
    gap_start("returning from playing")


def save_users(data: dict[str, User_Info], path: Path):
    # Convert dataclass instances to dicts recursively
    # If your dataclass has nested dataclasses, use a recursive helper or dataclasses.asdict()
    serializable_data = {user_id: asdict(info) for user_id, info in data.items()}

    with open(path, "w") as f:
        tomlkit.dump(serializable_data, f)


def load_users(path: Path) -> dict[str, User_Info]:
    # Use tomllib (binary mode) for reading if you only need data
    # Use tomlkit (text mode) if you need to preserve comments while editing
    try:
        with open(path, "rb") as f:
            data = tomlkit.load(f)
    except Exception as e:
        return {}

    # Reconstruct dataclasses
    return {user_id: User_Info(**info) for user_id, info in data.items()}


def create_presentation(user_info: User_Info):
    global USER_PRESENTATION
    presentation_text: str = f"{user_info.TTSname}  says"
    USER_PRESENTATION[user_info.name] = generate_audio(
        TTStext=presentation_text,
        TTSvoice=CONFIG.PRESENTATION_VOICE,
        TTSrate=CONFIG.PRESENTATION_RATE,
        TTSpitch=CONFIG.PRESENTATION_PITCH,
        TTSvolume=CONFIG.PRESENTATION_VOLUME,
    )


# check is _CHATUSER_CPNFIG_FILE exists
def read_TTSuserconfig():
    global USERS
    global USER_PRESENTATION
    if os.path.isfile(CONFIG.CHATUSER_CONFIG_FILE):
        USERS = load_users(Path(CONFIG.CHATUSER_CONFIG_FILE))
        for u in USERS.values():  # removing all used voices, leaving at least one.
            t: User_Info = u
            if len(ALLVOICES) > 0:
                try:
                    ALLVOICES.remove(t.voice)
                except Exception:
                    pass
            create_presentation(t)

        if len(ALLVOICES) == 0:
            load_voicenames()

    else:
        USERS = {}


def cache_beep():
    # pregenerate beep
    global BEEP_AUDIO
    with open(CONFIG.BEEP_SOUND, "rb") as f:
        BEEP_AUDIO = f.read()


def play_audio(audio_byte_stream):

    process = subprocess.Popen(
        [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel",
            "quiet",
            "-i",
            "pipe:0",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    process.stdin.write(audio_byte_stream)
    process.stdin.close()
    process.wait()


def get_author_info(author_name) -> User_Info:
    global USERS
    global ALLVOICES
    global ALL_CONFIG

    user = author_name[1:]  # remove the @

    if user not in USERS.keys():
        TTSuser = user.replace("_", " ")

        newuser = User_Info(
            name=user,
            TTSname=TTSuser,
            voice=ALLVOICES.pop(),
            pitch=CONFIG.USER_PITCH_DEFAULT,
            rate=CONFIG.USER_RATE_DEFAULT,
            volume=CONFIG.USER_DEFAULT_VOLUME,
        )

        if len(ALLVOICES) == 0:
            # no more voices. Reload all to start over
            load_voicenames()

        if newuser.name in ALL_CONFIG["predefined_users"].keys():
            value = ALL_CONFIG["predefined_users"][newuser.name].pop(0)
            if value != "None":
                newuser.TTSname = value
            value = ALL_CONFIG["predefined_users"][newuser.name].pop(0)
            if value != "None":
                newuser.voice = value
            value = ALL_CONFIG["predefined_users"][newuser.name].pop(0)
            if value != "None":
                newuser.rate = value
            value = ALL_CONFIG["predefined_users"][newuser.name].pop(0)
            if value != "None":
                newuser.pitch = value
            value = ALL_CONFIG["predefined_users"][newuser.name].pop(0)
            if value != "None":
                newuser.volume = value

        USERS[user] = newuser
        save_users(USERS, Path(CONFIG.CHATUSER_CONFIG_FILE))
        create_presentation(newuser)
    return USERS[user]


def check_beep():
    global LASTTIME
    newtime = time.perf_counter()
    if newtime - LASTTIME > CONFIG.BEEP_RESET_DELAY:
        play_audio(BEEP_AUDIO)
        pause_time = CONFIG.BEEP_PAUSE - (time.perf_counter() - newtime)
        time.sleep(max(pause_time, 0))


def TTSmessage(message):
    global LASTUSER
    global CONFIG
    global LASTTIME
    gap_start("getauthorinfo")
    user_info = get_author_info(message.author.name)
    gap_end("return from getauthorinfo")
    # TD : Add check for parameter beep
    if CONFIG.BEEP == "Enabled":
        gap_start("Playing the beep")
        check_beep()
        gap_end("beep played")
    text = message.message

    presentation = None
    if LASTUSER != user_info.name:
        LASTUSER = user_info.name
        try:
            presentation = USER_PRESENTATION[user_info.name]
        except Exception:
            create_presentation(user_info)

    gap_start("calling TTS player")
    generate_and_play_audio(
        TTStext=text,
        TTSvoice=user_info.voice,
        TTSrate=user_info.rate,
        TTSpitch=user_info.pitch,
        TTSvolume=user_info.volume,
        presentation=presentation,  # will be none if same user as last message
    )
    gap_end("Return from TTS player")
    LASTTIME = time.perf_counter()


def TestTiming():
    CONFIG.GAP_MONITOR = "Enabled"
    activate_gap()
    load_voicenames()
    gap_start("generate presentation")
    testp = generate_audio(
        TTStext="em beware says",
        TTSvoice=CONFIG.PRESENTATION_VOICE,
        TTSrate=CONFIG.PRESENTATION_RATE,
        TTSpitch=CONFIG.PRESENTATION_PITCH,
        TTSvolume=CONFIG.PRESENTATION_VOLUME,
    )
    gap_end("presentation generated")
    gap_start("Before loop")
    for v in ALLVOICES:
        print(f"Module_TTSbot - testing {v} ")
        gap_end(f"start of loop for {v}")
        gap_start("Call Player")
        generate_and_play_audio(
            TTStext=f"This is a test with {v} voice",
            TTSvoice=v,
            TTSrate=CONFIG.PRESENTATION_RATE,
            TTSpitch=CONFIG.PRESENTATION_PITCH,
            TTSvolume=CONFIG.PRESENTATION_VOLUME,
            presentation=testp,
        )
        gap_end("Return from Player")
        gap_start("End of loop")


def main():
    global CONFIG
    global USERS
    global LOG
    global ARGS
    global ALL_CONFIG
    print(f"Module_TTSbot - Loading config from {MAIN_CONFIG_FILE}")
    ALL_CONFIG = readconfig(MAIN_CONFIG_FILE)
    CONFIG = ALL_CONFIG.TTSbot
    print(f"Module_TTSbot - Logging event to {CONFIG.EVENTLOG}")
    LOG = logger.get_logger(__file__, logger.DEBUG, CONFIG.EVENTLOG)

    if CONFIG.TESTTIMING == "Enabled":
        LOG.info("starting timing tests")
        TestTiming()
        exit()

    if CONFIG.GAP_MONITOR == "Enabled":
        LOG.info("Activating gap monitor")
        activate_gap()

    parser = argparse.ArgumentParser(
        prog=f"{__file__}", description="TTSbot for youtube", epilog="a mbeware monstruosity"
    )
    parser.add_argument("--streamid", help="Start monitoring the live stream")
    ARGS = parser.parse_args()

    # read voicelist
    load_voicenames()
    LOG.info(f"{len(ALLVOICES)} voices loaded")
    # read existing users
    read_TTSuserconfig()
    LOG.info(f"{len(USERS)} users loaded")
    # cache sounds
    LOG.info("Caching beep sound")
    cache_beep()

    if not ARGS.streamid:
        if "STREAMID" in ALL_CONFIG["GLOBAL"].keys():
            LOG.info(f"Starting with streamid from config file : {CONFIG.STREAMID}")
            ARGS.streamid = str(CONFIG.STREAMID)
        else:
            ARGS.streamid = "PCOOSewAYMc"  # for testing.
            LOG.info(f"Starting with hardcoded streamid {ARGS.streamid}")
    else:
        LOG.info(f"Starting with commandline streamid : {ARGS.streamid}")
    print("Module_TTSbot Ready. Waiting for messages")
    chatreader(TTSmessage, ARGS.streamid, "TTSbot")


if __name__ == "__main__":
    print(f"Module_TTSbot Version : {Path('version.txt').read_text()}")
    main()
