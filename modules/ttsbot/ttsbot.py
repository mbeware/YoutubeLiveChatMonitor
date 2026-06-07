import asyncio
import edge_tts
from dataclasses import dataclass, asdict
import random
from pathlib import Path
import time
import tomlkit
import os
import logging
import sys


_BEEP_PAUSE = 1
_ENGLISH_VOICE_LIST = "LimitedEnglishVoices.txt"
_SELECTED_PITCHES = ["-2Hz", "+0Hz", "+2Hz"]
_SELECTED_RATES = ["-5%", "+0%", "+5%"]
_CHATUSER_CONFIG_FILE = "chatuser_config.toml"
_PRESENTATION_VOICE = "en-US-AriaNeural"
_PRESENTATION_PITCH = "+0Hz"
_PRESENTATION_RATE = "+0%"
_USER_PITCH_DEFAULT = "+0Hz"
_USER_RATE_DEFAULT = "+0%"
_BEEP_SOUND = "beep.mp3"
_BEEP_RESET_DELAY = 20
_TTSBOT_LOG = "ttsbot.log"

MODULE_FOLDER = Path(__file__).resolve().parent

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File Handler (All levels)
file_handler = logging.FileHandler(_TTSBOT_LOG)
file_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Attach handlers
logger.addHandler(file_handler)

logger.debug("Started TTSbot")


def add_config_to_context(context):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    print("Adding ttbot_config to context")
    ttsbot_config = {}
    ttsbot_config["beep_pause"] = _BEEP_PAUSE
    ttsbot_config["english_voice_list"] = _ENGLISH_VOICE_LIST
    ttsbot_config["selected_pitches"] = _SELECTED_PITCHES
    ttsbot_config["selected_rates"] = _SELECTED_RATES
    ttsbot_config["chatuser_config_file"] = _CHATUSER_CONFIG_FILE
    ttsbot_config["beep_reset_delay"] = _BEEP_RESET_DELAY
    ttsbot_config["beep_pause"] = _PRESENTATION_VOICE
    ttsbot_config["beep_pause"] = _PRESENTATION_PITCH
    ttsbot_config["beep_pause"] = _PRESENTATION_RATE
    ttsbot_config["beep_pause"] = _USER_PITCH_DEFAULT
    ttsbot_config["beep_pause"] = _USER_RATE_DEFAULT
    ttsbot_config["beep_sound"] = _BEEP_SOUND

    context["ttsbot_config"] = ttsbot_config
    print("ttsbot_config added to context")
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")


print(" ......loading voices")

voicesfile = MODULE_FOLDER / _ENGLISH_VOICE_LIST  # remember, MODULE_FOLDER type is a Path, not a string.
# voicesfile = Path(_ENGLISH_VOICE_LIST) # this is what we have to do, when we dont already have a Path type.


allvoices_raw = voicesfile.read_text().splitlines()
allvoices = []
for v in allvoices_raw:
    allvoices.append(v.strip())

print(f"loading module TTS ........ {len(allvoices)} voices loaded")
allpitches = _SELECTED_PITCHES
allrates = _SELECTED_RATES


LASTUSER = ""


@dataclass
class User_Info:
    name: str
    TTSname: str
    voice: str
    rate: str
    pitch: str


user_presentation: dict[str, bytes] = {}


def save_users(data: dict[str, User_Info], path: Path):
    # Convert dataclass instances to dicts recursively
    # If your dataclass has nested dataclasses, use a recursive helper or dataclasses.asdict()
    serializable_data = {user_id: asdict(info) for user_id, info in data.items()}

    with open(path, "w") as f:
        tomlkit.dump(serializable_data, f)


# Usage
# save_users(users, Path("users.toml"))


def load_users(path: Path) -> dict[str, User_Info]:
    # Use tomllib (binary mode) for reading if you only need data
    # Use tomlkit (text mode) if you need to preserve comments while editing
    with open(path, "rb") as f:
        data = tomlkit.load(f)

    # Reconstruct dataclasses
    return {user_id: User_Info(**info) for user_id, info in data.items()}


# Usage
# loaded_users = load_users(Path("users.toml"))
# print(loaded_users["user1"].name)  # Output: Alice


# initialisation (executed on module load)
# check is _CHATUSER_CPNFIG_FILE exists
print("loading module TTS .....loading chatuser configs")

if os.path.isfile(_CHATUSER_CONFIG_FILE):
    users: dict[str, User_Info] = load_users(Path(_CHATUSER_CONFIG_FILE))
    for u in users.items():  # removing all used voices, leaving at least one.
        t: User_Info = u
        if len(allvoices) > 1:
            try:
                allvoices.remove(t.voice)
            except Exception:
                pass
else:
    users: dict[str, User_Info] = {}


# pregenerate beep
print("loading module TTS .....generating beep")

with open(_BEEP_SOUND, "rb") as f:
    beep_audio = f.read()


async def play_beep():
    global beep_audio
    process = await asyncio.create_subprocess_exec(
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "quiet",
        "-i",
        "pipe:0",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    process.stdin.write(beep_audio)
    await process.stdin.drain()
    process.stdin.close()
    await process.wait()


async def play_file(file):
    try:
        process = await asyncio.create_subprocess_exec(
            "ffplay", "-nodisp", "-autoexit", file, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )

        return process
    except FileNotFoundError:
        print("ffplay not found. Install ffmpeg to enable playback.")


async def generate_tts_bytes(text, voice, rate="+0%", pitch="+0Hz"):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    import edge_tts

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)

    audio = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])

    logger.debug(f"Exited {sys._getframe().f_code.co_name}")
    return bytes(audio)


async def text_to_speech_async(
    text: str, voice: str = "en-US-AriaNeural", rate: str = "+0%", pitch: str = "+0Hz", presentation=None
):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    if not text.strip():
        logger.debug(f"Exited {sys._getframe().f_code.co_name}")
        return

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
        process.stdin.write(presentation)
        # await process.stdin.drain()

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)

    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                process.stdin.write(chunk["data"])
                await process.stdin.drain()
    except Exception:
        pass
    finally:
        process.stdin.close()
        await process.wait()
        logger.debug(f"exited {sys._getframe().f_code.co_name}")


def false_random(key, list):
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    nb = len(list)
    ascii_sum = sum(ord(char) for char in key)
    numkey = ascii_sum % nb
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")
    return list[numkey]


async def get_author_info(author_name) -> User_Info:
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    global users
    user = author_name[1:]  # remove the @

    if user not in users.keys():
        TTSuser = user.replace("_", " ")
        if user == "Maple-Circuit-Live":
            TTSuser = "Maple Circuit"
        elif user == "mbeware":
            TTSuser = "embeware"

        newuser = User_Info(
            name=user,
            TTSname=TTSuser,
            voice=false_random(user, allvoices).strip(),
            pitch=_USER_PITCH_DEFAULT,
            rate=_USER_RATE_DEFAULT,
        )
        if len(allvoices) > 1:  # never remove the last voice
            allvoices.remove(newuser.voice)

        users[user] = newuser
        save_users(users, Path(_CHATUSER_CONFIG_FILE))

    presentation_text: str = f"{users[user].TTSname}  says"
    user_presentation[user] = await generate_tts_bytes(
        text=presentation_text, voice=_PRESENTATION_VOICE, rate=_PRESENTATION_RATE, pitch=_PRESENTATION_PITCH
    )

    logger.debug(f"Exited {sys._getframe().f_code.co_name}")
    return users[user]


LASTTIME = 0


async def check_beep():
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    global LASTTIME
    newtime = time.perf_counter()

    global LASTTIME
    if newtime - LASTTIME > _BEEP_RESET_DELAY:
        await play_beep()
        await asyncio.sleep(_BEEP_PAUSE)
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")


async def process_message(message, context):

    # This is a Quick and dirty version of what I want to do
    # Missing stuff :
    # Rate limiting
    # Spam limiting
    # User validation
    # User Configuration
    # User Moderation

    # In this version, a "voice" is randomly assigned to each user
    # That assignation is not saved and will probably be different the next time the tool is used.
    logger.debug(f"Entered {sys._getframe().f_code.co_name}")
    config = context["config"]

    TTS_config = config["TTS"]

    user_info = await get_author_info(message.author.name)
    await check_beep()
    text = message.message
    global LASTUSER

    presentation = None
    if LASTUSER != user_info.name:
        LASTUSER = user_info.name
        presentation = user_presentation[user_info.name]

    await text_to_speech_async(
        text=text,
        voice=user_info.voice,
        rate=user_info.rate,
        pitch=user_info.pitch,
        presentation=presentation,  # will be none if same user as last message
    )
    global LASTTIME
    LASTTIME = time.perf_counter()
    logger.debug(f"Exited {sys._getframe().f_code.co_name}")


print("loading module TTS", end="")
