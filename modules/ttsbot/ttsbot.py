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
    output_file: Optional[str] = None,
    play_audio: bool = False
):


    if not text.strip():
        raise ValueError("Text cannot be empty")

    # Create temp file if needed
    if output_file is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_file = tmp.name
        tmp.close()

    # Generate audio
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )

    await communicate.save(output_file)

    # Optional async playback (non-blocking)
    if play_audio:
        try:
            await asyncio.create_subprocess_exec(
                "ffplay",
                "-nodisp",
                "-autoexit",
                "beep.mp3",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.sleep(2)

            await asyncio.create_subprocess_exec(
                "ffplay",
                "-nodisp",
                "-autoexit",
                output_file,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except FileNotFoundError:
            print("ffplay not found. Install ffmpeg to enable playback.")

    return output_file

async def process_message(message):
    text = message.message
    if message.author.name == "@mbeware":
        file_path = await text_to_speech_async(text=text,  output_file="test.mp3" , voice="en-US-GuyNeural",    rate="+10%",    pitch="+2Hz",    play_audio=True)

        print("Saved to:", file_path)
    
 