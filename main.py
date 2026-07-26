from MyClient import bot, handler, token

if __name__ == "__main__":
    assert token
    bot.run(token, log_handler=handler)
