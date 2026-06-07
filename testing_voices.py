from pathlib import Path
import logging
import argparse
import subprocess


_ENGLISH_VOICE_LIST = "LimitedEnglishVoices.txt"
_LOG = f"{__file__}.log"


def start_logger():
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # File Handler (All levels)
    file_handler = logging.FileHandler(_LOG)
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Attach handlers
    logger.addHandler(file_handler)
    return logger


logger = start_logger()
logger.debug(f"Started {__file__}")


def tts_play(text, voice):
    import asyncio  # only used internally, hidden from your logic
    import edge_tts

    async def generate_audio():
        communicate = edge_tts.Communicate(text=text, voice=voice)
        audio = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]

        return audio

    # Run async internally but expose sync API
    audio_data = asyncio.run(generate_audio())

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

    process.stdin.write(audio_data)
    process.stdin.close()
    process.wait()


def main():

    parser = argparse.ArgumentParser(prog=f"{__file__}", epilog="a mbeware monstruosity")

    parser.add_argument("--voicefile")

    args = parser.parse_args()

    if not args.voicefile:
        args.voicefile = Path("modules") / "ttsbot" / _ENGLISH_VOICE_LIST

    print(f" Playing voices from {args.voicefile}")
    voicesfile = args.voicefile
    allvoices_raw = voicesfile.read_text().splitlines()
    for v in allvoices_raw:
        print(f"testing {v.strip()}")
        tts_play("This is a test for text to speech voices", v.strip())


if __name__ == "__main__":
    main()
