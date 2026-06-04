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


async def text_to_speech_async(
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "0%",
    output_file: Optional[str] = "TTS.mp3",
    play_audio: bool = False,
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
    delay_async = 2
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
    config = context["config"]
    TTS_config = config["TTS"]

    voice=TTS_config["voice"]
    rate=TTS_config["rate"]
    pitch=TTS_config["pitch"]
    play_audio=TTS_config["play_audio"] == "True"


    text = message.message
    file_path = None
    if message.author.name == "@mbeware":
        file_path = await text_to_speech_async(text=text , voice=voice,    rate=rate,    pitch=pitch,    play_audio=play_audio)
    
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
