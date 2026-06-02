import pytchat


# from pytchat doc 
# https://github.com/taizan-hokuto/pytchat

chat = pytchat.create(video_id="_TzT6UD_9D4")
while chat.is_alive():
    for c in chat.get().sync_items():
        print(f"{c.datetime} [{c.author.name}]- {c.message}")