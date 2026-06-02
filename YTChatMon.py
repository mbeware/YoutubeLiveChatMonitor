
# Reader
# Dispatcher
## DynamicModules
## Mod:Logguer
## Mod:Commander
### Admin commands
### SuperMod commands
### Moderator commands
### User commands
## Mod:Text2Voice

import pytchat
import signal
import asyncio #Less issue with asyncio, but less effective

async def reader(chat_queue,event_stoprequested):
    
    chat = pytchat.create(video_id="DkZwyeYoT-4")
    try:
        while chat.is_alive() and not event_stoprequested.is_set():
            for c in chat.get().sync_items():
                await chat_queue.put(c) 
            await asyncio.sleep(0.5)
    except KeyboardInterrupt:
        event_stoprequested.set()

    except Exception as e:
        print(f"{e} exception (reader)")


async def dispatcher(chat_queue,event_stoprequested):
    try:
        while not event_stoprequested.is_set():

            c=None
            try:
                c=await asyncio.wait_for(chat_queue.get(),timeout=0.5)
                await asyncio.sleep(0.5)
            except TimeoutError: 
                print("No new messages")
                
            except KeyboardInterrupt:
                event_stoprequested.set()
                return
            except Exception as e:
                print(f"{e}")
          
            if c: 
                print(f"{c.datetime} [{c.author.name}]- {c.message}")
                
          
    except KeyboardInterrupt:
        event_stoprequested.set()
    
    except Exception as e:
        print(f"{e} exception (dispatcher)")
        # event_stoprequest.set() # this will break out of the loop.
        
        
        

async def main():


    # Reader will put messages in a queue
    # Dispatcher will read from queue and invoque appropriate module

    # create queue
    chat_queue = asyncio.Queue(0)
    event_stopRequested = asyncio.Event()

    reader_t = asyncio.create_task(reader(chat_queue,event_stopRequested))
    dispatcher_t = asyncio.create_task(dispatcher(chat_queue,event_stopRequested))
        

    try:
        await asyncio.gather(dispatcher_t,reader_t)
    except Exception as e:
        print(f"{e} exception (main)")

    event_stopRequested.set()
    


        
if __name__ == "__main__":
    asyncio.run(main())
else:
    print("{__name__} loaded as module")


