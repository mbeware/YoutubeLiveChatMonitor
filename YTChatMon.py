
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
import os



async def reader(chat_queue,YoutubeLiveStreamID):
    
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

async def dispatcher(chat_queue,modules):

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
                        tasks.append(func(message))
                    else:
                        # wrap sync in thread to avoid blocking
                        loop = asyncio.get_running_loop()
                        tasks.append(loop.run_in_executor(None, func, message))
            if len(tasks) > 0 :
                await asyncio.gather(*tasks, return_exceptions=True)

                
    except asyncio.CancelledError:
        pass  # We have been cancelled. What did we do????

    # we should send a message to reader to tell it that we dont dispatch anymore...

        
     
        
async def start_monitor(args,modules):
    # Reader will put messages in a queue
    # Dispatcher will read from queue and invoque appropriate module

    # create queue
    chat_queue = asyncio.Queue(0)

    reader_t = asyncio.create_task(reader(chat_queue,args.videoid))
    dispatcher_t = asyncio.create_task(dispatcher(chat_queue,modules))
        

    try:
        await asyncio.gather(dispatcher_t,reader_t)

    except KeyboardInterrupt:
        reader_t.cancel()
        dispatcher_t.cancel()
        await asyncio.gather(dispatcher_t, reader_t, return_exceptions=True)

def create_config():
    config_path = Path.home() / ".config" / "YoutubeLiveChatMonitor" 
    config_file = config_path / "config.toml" 

    
    if config_file.exists():
        raise FileExistsError(f"Config file already exists: {config_path}")

    # Creates all intermediate directories if they don't exist
    os.makedirs(config_path , exist_ok=True)


    
    # Create a new TOML document
    config = tomlkit.document()
    config_general = tomlkit.table()
    config_general["modules_list"] = []
    config.add("general",config_general)
    config.add(tomlkit.comment('modules_list = ["module1", "module2"]'))
    config.add(tomlkit.comment("[module1]") )
    config.add(tomlkit.comment('file_path = "path/module1.py"'))
    config.add(tomlkit.comment('[module2]'))
    config.add(tomlkit.comment('file_path = "path/module2.py"'))

    # Write to file
    with open(config_file, "w") as toml_file:
        toml_file.write(tomlkit.dumps(config))



def main():
    parser = argparse.ArgumentParser(
                    prog='YTChatMon',
                    description='Monitor and act on live youtube chat',
                    epilog='a mbeware monstruosity')

    parser.add_argument('--install',action='store_true',help='Create configuration files')
    parser.add_argument('--videoid',help='Start monitoring the live stream') 
    parser.add_argument('--debug',help=argparse.SUPPRESS) 
    
    args = parser.parse_args()

    if args.install:
        create_config()
        return 0
    
    modules = load_modules_from_config()



    if not args.videoid: 
        args.videoid='FN_2He-LL5g' # for testing. 

    asyncio.run(start_monitor(args,modules))
    return 0 
    
    
    
 

        
if __name__ == "__main__":
    exit(main())
else:
    print("{__name__} loaded as module")


