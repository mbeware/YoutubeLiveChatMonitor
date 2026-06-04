def process_message(message):
    with open("l",mode="a") as f:
        f.write(f"{message.datetime} [{message.author.name}]- {message.message}\n")
