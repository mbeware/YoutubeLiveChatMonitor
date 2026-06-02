
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
import asyncio #Less issue with asyncio, but less effective

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

async def dispatcher(chat_queue):

    try:
        while True:
        
            c=await chat_queue.get() #Blocking/wait forever
            
            if c is None: 
                break

            print(f"{c.datetime} [{c.author.name}]- {c.message}")
                
    except asyncio.CancelledError:
        pass  # We have been cancelled. What did we do????
        
     
        
        

async def main():
    YoutubeLiveStreamID = "0SqBi7qdK_c"

    # Reader will put messages in a queue
    # Dispatcher will read from queue and invoque appropriate module

    # create queue
    chat_queue = asyncio.Queue(0)

    reader_t = asyncio.create_task(reader(chat_queue,YoutubeLiveStreamID))
    dispatcher_t = asyncio.create_task(dispatcher(chat_queue))
        

    try:
        await asyncio.gather(dispatcher_t,reader_t)

    except KeyboardInterrupt:
        reader_t.cancel()
        dispatcher_t.cancel()
        await asyncio.gather(dispatcher_t, reader_t, return_exceptions=True)


        
if __name__ == "__main__":
    asyncio.run(main())
else:
    print("{__name__} loaded as module")


