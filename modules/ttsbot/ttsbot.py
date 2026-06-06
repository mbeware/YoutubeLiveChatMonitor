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

print(" .....loading voices")
voicesfile = Path(__file__).resolve().parent / "LimitedEnglishVoices.txt"
allvoices = voicesfile.read_text().splitlines() 
allpitches = ["-2Hz","+0Hz","+2Hz"]
allrates = ["-5%","+0%","+5%"]


lastuser = ""
lasttime = 0

@dataclass
class UserVoice:
    name : str
    voice : str
    rate : str
    pitch : str
    presentation : bytes



# pregenerate beep
print("loading module TTS .....generating beep")

with open("beep.mp3", "rb") as f:
    beep_audio = f.read()

async def play_beep():
    global beep_audio
    process = await asyncio.create_subprocess_exec(
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel", "quiet",
        "-i", "pipe:0",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    process.stdin.write(beep_audio)
    await process.stdin.drain()
    process.stdin.close()
    await process.wait()


async def play_file(file):
    try:
        process = await asyncio.create_subprocess_exec( "ffplay",
                                                        "-nodisp",
                                                        "-autoexit",
                                                        file,
                                                        stdout=asyncio.subprocess.DEVNULL,
                                                        stderr=asyncio.subprocess.DEVNULL)

        return process
    except FileNotFoundError:
        print("ffplay not found. Install ffmpeg to enable playback.")
    
async def generate_tts_bytes(text, voice, rate="+0%", pitch="+0Hz"):
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )

    audio = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])

    return bytes(audio)

async def text_to_speech_async( text: str,
                                voice: str = "en-US-AriaNeural",
                                rate: str = "+0%",
                                pitch: str = "+0Hz",
                                presentation = None):
    if not text.strip():
        return

    process = await asyncio.create_subprocess_exec( "ffplay",
                                                    "-nodisp",
                                                    "-autoexit",
                                                    "-loglevel", "quiet",
                                                    "-i", "pipe:0",  # read from stdin
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.DEVNULL,
                                                    stderr=asyncio.subprocess.DEVNULL
                                                    )
    if presentation:
        process.stdin.write(presentation)
        #await process.stdin.drain()

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )

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


    user = message.author.name[1:] # remove the @
    if user == "Maple-Circuit-Live": 
        user = "Maple Circuit"
 
    if user not in users.keys():
        presentation_text = user + " says"
        newuser = UserVoice(name = user,       
                            voice = random.choice(allvoices).strip(),
                            pitch = random.choice(allpitches).strip(),
                            rate = random.choice(allrates).strip(),
                            presentation = await generate_tts_bytes(text=presentation_text,voice="en-US-AriaNeural",rate="+0%",pitch="+0Hz"))
        users[user] = newuser

    voice = users[user].voice
    rate = users[user].rate
    pitch = users[user].pitch

    newtime = time.perf_counter()
    beep = True

    global lasttime 
    beep_reset_delay=20
    if newtime - lasttime < beep_reset_delay:
        beep = False
    lasttime = newtime
    beep_pause = 1

    if beep:
        await play_beep()
        await asyncio.sleep(beep_pause) 


    text = message.message
    global lastuser
    
    presentation = None
    if lastuser != user: 
        lastuser = user
        presentation = users[user].presentation

    
    await text_to_speech_async(text=text,voice=voice,rate=rate,pitch=pitch,presentation=presentation)
    
            

print("loading module TTS",end="")
        
