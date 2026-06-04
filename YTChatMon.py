
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
from YTChatMon_loadmodules import load_modules_from_config 


import argparse
from pathlib import Path
import pytchat
import asyncio #Less issue with asyncio, but less effective
import inspect
import tomlkit
import tomllib
import os



async def reader(context ):
    chat_queue = context["chat_queue"]
    YoutubeLiveStreamID = context["args"].streamid

    chat = pytchat.create(video_id=YoutubeLiveStreamID)
    try:
        while chat.is_alive():
            for c in chat.get().sync_items():
                await chat_queue.put(c) 
            await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        pass

    except Exception as e:
        print(f"{e} exception (reader)")

    finally:
        await chat_queue.put(None) 

async def dispatcher(context):
    chat_queue = context["chat_queue"]
    modules = context["modules"]
    try:
        while True:
        
            message=await chat_queue.get() #Blocking/wait forever
            
            if message is None: 
                break


            tasks = []
            for name, module in modules.items():
                if hasattr(module, "process_message"):
                    func = module.process_message

                    if inspect.iscoroutinefunction(func):
                        tasks.append(func(message,context))
                    else:
                        # wrap sync in thread to avoid blocking
                        loop = asyncio.get_running_loop()
                        tasks.append(loop.run_in_executor(None, func, message, context))
            if len(tasks) > 0 :
                await asyncio.gather(*tasks, return_exceptions=True)

                
    except asyncio.CancelledError:
        pass  # We have been cancelled. What did we do????

    # we should send a message to reader to tell it that we dont dispatch anymore...

        
     
        
async def start_monitor(context):
    # Reader will put messages in a queue
    # Dispatcher will read from queue and invoque appropriate module
    
    # create queue
    chat_queue = asyncio.Queue(0)
    context["chat_queue"] = chat_queue
    reader_t = asyncio.create_task(reader(context))
    dispatcher_t = asyncio.create_task(dispatcher(context))
         

    try:
        await asyncio.gather(dispatcher_t,reader_t)

    except KeyboardInterrupt:
        reader_t.cancel()
        dispatcher_t.cancel()
        await asyncio.gather(dispatcher_t, reader_t, return_exceptions=True)

def create_config():
    config_path = Path.home() / ".config" / "YoutubeLiveChatMonitor" 
    config_file = config_path / "config.toml" 

    # Creates all intermediate directories if they don't exist
    os.makedirs(config_path , exist_ok=True)
    
    if config_file.exists():
        raise FileExistsError(f"Config file already exists: {config_path}")


    # Create a new TOML document
    config = tomlkit.document()
    config_general = tomlkit.table()
    config_general["modules_list"] = ["printmsg","TTS"]
    config_printmsg = tomlkit.table()
    config_printmsg.add(('file_path = "printmsg/printmsg.py"'))
    config_tts = tomlkit.table()
    config_tts.add(('file_path = "ttsbot/ttsbot.py"'))
   
    config.add("general",config_general)
    config.add("printmsg",config_printmsg)
    config.add("ttsbot",config_tts)

    # Write to file
    with open(config_file, "w") as toml_file:
        toml_file.write(tomlkit.dumps(config))

def readconfig():
    config_path = Path.home() / ".config" / "YoutubeLiveChatMonitor" / "config.toml"

    if not config_path.exists():
        raise FileNotFoundError(f"No config file: {config_path}\nRun YTChatMon --install to create it")

    
    with config_path.open("rb") as f:
        config = tomllib.load(f)
        return config


def main():
    parser = argparse.ArgumentParser(
                    prog='YTChatMon',
                    description='Monitor and act on live youtube chat',
                    epilog='a mbeware monstruosity')

    parser.add_argument('--install',action='store_true',help='Create configuration files')
    parser.add_argument('--streamid',help='Start monitoring the live stream') 
    parser.add_argument('--debug',help=argparse.SUPPRESS) 
    
    args = parser.parse_args()

    if args.install:
        create_config()
        return 0
    
    context={}
    context["args"] = args
    context["config"]=readconfig()

    context["modules"] = load_modules_from_config(context)

    if not args.streamid: 
        args.streamid='QlwUUv9niuM' # for testing. 

    asyncio.run(start_monitor(context))
    return 0 
        
if __name__ == "__main__":
    exit(main())
else:
    print("{__name__} loaded as module")


