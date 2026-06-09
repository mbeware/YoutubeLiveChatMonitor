from logger import logger
from YTChatMon_Submodule_ChatReader import chatreader
from YTChatMon_Submodule_Configfile import readconfig, ConfigObject

from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import asyncio
import edge_tts
import time
import tomlkit
import os
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
LOG: logger.Logger
ARGS = None
LOG_TIMING: logger.Logger
ALL_CONFIG: ConfigObject
MAIN_CONFIG_FILE = "YTChatMon.toml"


def remove_duplicate_words(text, only_emojii=True):
    #
    text = text.replace("::", ": :")  # make sure we have a space between emojii as space is the splitter
    tokens = text.split()
    if not tokens:
        return text

    result = []
    index_current_token = 0
    index_next_token = 1  # Just to make the linter stop complaining about "Unbound Variable"

    while index_current_token < len(tokens):
        count = 0

        current_token = tokens[index_current_token]
        if (current_token[0] == ":" and current_token[-1] == ":") or not only_emojii:
            count = 1

            index_next_token = index_current_token + 1
            while index_next_token < len(tokens) and tokens[index_next_token] == current_token:
                count += 1
                index_next_token += 1

        if count > 1:
            result.append(f"{count}")
            result.append(current_token)
            index_current_token = index_next_token
        else:
            result.append(current_token)
            index_current_token += 1

    return " ".join(result)


def test_remove_duplicate_words():
    tests = [
        "The gift was a trap :snake: :snake:",
        ":time: :time: :time:",
        "This is a :test:",
        "The :pool: is near the other :pool: in the back",
        "3 :o: :o: :o: :o: 4",
        "ABC ABC ABC ABC",
        ":aaa: :aaa: :bbb: :bbb: :aaa: :aaa:",
        ":aaa: :bbb: :aaa: :bbb:",
    ]
    print("Remove only duplicate emojii")
    for t in tests:
        print(f"Input:  {t}")
        print(f"Output: {remove_duplicate_words(t, only_emojii=True)}")
        print("-" * 30)
    print("Remove all duplicate words")
    for t in tests:
        print(f"Input:  {t}")
        print(f"Output: {remove_duplicate_words(t, only_emojii=False)}")
        print("-" * 30)
    exit()


# test_remove_duplicate_words()


def load_voicenames():
    global ALLVOICES
    global ALLVOICES_CACHE

    if len(ALLVOICES_CACHE) > 0:
        ALLVOICES = ALLVOICES_CACHE.copy()
        return

    voicesfile = MODULE_FOLDER / CONFIG.ENGLISH_VOICE_LIST  # type: ignore
    # remember, MODULE_FOLDER type is a Path, not a string.
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
        if presentation:
            process.stdin.write(presentation)  # type: ignore
            await process.stdin.drain()  # type: ignore
        communicate = edge_tts.Communicate(text=TTStext, voice=TTSvoice, rate=TTSrate, pitch=TTSpitch, volume=TTSvolume)
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    process.stdin.write(chunk["data"])  # type: ignore
                    await process.stdin.drain()  # type: ignore
        except Exception:
            pass
        finally:
            process.stdin.close()  # type: ignore
            await process.wait()

    asyncio.run(play_audio_async())


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
    except Exception:
        return {}

    # Reconstruct dataclasses
    return {user_id: User_Info(**info) for user_id, info in data.items()}


def create_presentation(user_info: User_Info):
    global USER_PRESENTATION
    presentation_text: str = f"{user_info.TTSname}  says"
    USER_PRESENTATION[user_info.name] = generate_audio(
        TTStext=presentation_text,
        TTSvoice=CONFIG.PRESENTATION_VOICE,  # pyright: ignore[reportOptionalMemberAccess]
        TTSrate=CONFIG.PRESENTATION_RATE,  # pyright: ignore[reportOptionalMemberAccess]
        TTSpitch=CONFIG.PRESENTATION_PITCH,  # pyright: ignore[reportOptionalMemberAccess]
        TTSvolume=CONFIG.PRESENTATION_VOLUME,  # pyright: ignore[reportOptionalMemberAccess]
    )


# check is _CHATUSER_CPNFIG_FILE exists
def read_TTSuserconfig():
    global USERS
    global USER_PRESENTATION
    if os.path.isfile(CONFIG.CHATUSER_CONFIG_FILE):  # pyright: ignore[reportOptionalMemberAccess]
        USERS = load_users(Path(CONFIG.CHATUSER_CONFIG_FILE))  # pyright: ignore[reportOptionalMemberAccess]
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
    with open(CONFIG.BEEP_SOUND, "rb") as f:  # pyright: ignore[reportOptionalMemberAccess]
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

    process.stdin.write(audio_byte_stream)  # type: ignore
    process.stdin.close()  # type: ignore
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
            pitch=CONFIG.USER_PITCH_DEFAULT,  # pyright: ignore[reportOptionalMemberAccess]
            rate=CONFIG.USER_RATE_DEFAULT,  # pyright: ignore[reportOptionalMemberAccess]
            volume=CONFIG.USER_DEFAULT_VOLUME,  # pyright: ignore[reportOptionalMemberAccess]
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
        save_users(USERS, Path(CONFIG.CHATUSER_CONFIG_FILE))  # pyright: ignore[reportOptionalMemberAccess]
        create_presentation(newuser)
    return USERS[user]


def check_beep():
    global LASTTIME
    newtime = time.perf_counter()
    if newtime - LASTTIME > CONFIG.BEEP_RESET_DELAY:  # pyright: ignore[reportOptionalMemberAccess]
        play_audio(BEEP_AUDIO)
        pause_time = CONFIG.BEEP_PAUSE - (time.perf_counter() - newtime)  # pyright: ignore[reportOptionalMemberAccess]
        time.sleep(max(pause_time, 0))


def TTSmessage(message):
    global LASTUSER
    global CONFIG
    global LASTTIME
    user_info = get_author_info(message.author.name)
    # TD : Add check for parameter beep
    if CONFIG.BEEP == "Enabled":  # pyright: ignore[reportOptionalMemberAccess]
        check_beep()
    text = message.message

    presentation = None
    if LASTUSER != user_info.name:
        LASTUSER = user_info.name
        try:
            presentation = USER_PRESENTATION[user_info.name]
        except Exception:
            create_presentation(user_info)

    if CONFIG.REMOVE_DUPLICATE_WORDS == "emojii_only":  # pyright: ignore[reportOptionalMemberAccess]
        only_emojii = True
    elif CONFIG.REMOVE_DUPLICATE_WORDS == "all":  # pyright: ignore[reportOptionalMemberAccess]
        only_emojii = False
    else:  # ONFIG.REMOVE_DUPLICATE_WORDS == "Disabled"
        only_emojii = None

    if only_emojii is not None:
        text = remove_duplicate_words(text, only_emojii=only_emojii)

    generate_and_play_audio(
        TTStext=text,
        TTSvoice=user_info.voice,
        TTSrate=user_info.rate,
        TTSpitch=user_info.pitch,
        TTSvolume=user_info.volume,
        presentation=presentation,  # will be none if same user as last message
    )
    LASTTIME = time.perf_counter()


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
            LOG.info(f"Starting with streamid from config file : {ALL_CONFIG['GLOBAL'].STREAMID}")
            ARGS.streamid = str(ALL_CONFIG["GLOBAL"].STREAMID)
        else:
            ARGS.streamid = "wXxDFWgvTpw"  # for testing.
            LOG.info(f"Starting with hardcoded streamid {ARGS.streamid}")
    else:
        LOG.info(f"Starting with commandline streamid : {ARGS.streamid}")
    print("Module_TTSbot Ready. Waiting for messages")
    chatreader(TTSmessage, ARGS.streamid, "TTSbot")


if __name__ == "__main__":
    print(f"Module_TTSbot Version : {Path('version.txt').read_text()}")
    main()
