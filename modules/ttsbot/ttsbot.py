import asyncio
import edge_tts
import tempfile
import os
import subprocess

import asyncio
import edge_tts
import tempfile
import subprocess
from typing import Optional
from dataclasses import dataclass
import random
from pathlib import Path
import time


# initialisation (executed on module load)
users = {}

voicesfile = Path(__file__).resolve().parent / "LimitedEnglishVoices.txt"
allvoices = voicesfile.read_text().splitlines() 
allpitches = ["-10Hz","-5Hz","+0Hz","+5Hz","+10Hz"]
allrates = ["-5%","+0%","+5%","+10%","+15%"]


lastuser = ""
lasttime = 0

@dataclass
class UserVoice:
    name : str
    voice : str
    rate : str
    pitch : str


async def text_to_speech_async(
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "0%",
    output_file: Optional[str] = "TTS.mp3",
    play_audio: bool = True,
    beep: bool = True,
    beep_delay: float = 1.5
):


    if not text.strip():
        raise ValueError("Text cannot be empty")

    # Create temp file if needed
    #if output_file is None:
    #    output_file = "TTS.mp3"
    #    tmp = tempfile.NamedTemporaryFile(delete=False, delete_on_close=False, suffix=".mp3")
    #    output_file = tmp.name
    #    tmp.close()


    process = None
    if play_audio and beep:
        try:
            process = await asyncio.create_subprocess_exec(
                "ffplay",
                "-nodisp",
                "-autoexit",
                "beep.mp3",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except FileNotFoundError:
            print("ffplay not found. Install ffmpeg to enable playback.")


    full_output_file = f"{tempfile.gettempdir()}/{output_file}"
    #full_output_file = "TTS.mp3"
    # Generate audio
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )
    
    await communicate.save(full_output_file)
    #await asyncio.sleep(delay_async)
    # Optional async playback (non-blocking)
    if play_audio:
        try:
            if beep:
                await asyncio.sleep(beep_delay)
            if process:
                await process.wait()
            process = await asyncio.create_subprocess_exec(
                "ffplay",
                "-nodisp",
                "-autoexit",
                full_output_file,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
        except FileNotFoundError:
            print("ffplay not found. Install ffmpeg to enable playback.")

    return full_output_file



async def process_message(message,context):

    # This is a Quick and dirty version of what I want to do
    # Missing stuff : 
    # Rate limiting
    # Spam limiting
    # User validation
    # User Configuration
    # User Moderation
    
    # In this version, a "voice" is randomly assigned to each user
    # That assignation is not saved and will probably be different the next time the tool is used.
     


    config = context["config"]
    TTS_config = config["TTS"]

    play_audio=TTS_config["play_audio"] == "True"

    user = message.author.name[1:] # remove the @
    if user == "Maple-Circuit-Live": 
        user = "Maple Circuit"
 
    if user not in users.keys():
        newuser = UserVoice(name = user,       
                            voice = random.choice(allvoices).strip(),
                            pitch = random.choice(allpitches).strip(),
                            rate = random.choice(allrates).strip())
        users[user] = newuser

    voice = users[user].voice
    rate = users[user].rate
    pitch = users[user].pitch

    newtime = time.perf_counter()
    beep = True

    global lasttime 

    if newtime - lasttime < 20:
        beep = False
    lasttime = newtime

    global lastuser

    if lastuser != user: 
        text = user + " says " + message.message
        lastuser = user
    else:
        text = message.message
    beep_delay = 1
    file_path = None
    file_path = await text_to_speech_async(text=text,voice=voice,rate=rate,pitch=pitch,beep=beep,beep_delay=beep_delay)
    
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
