import configparser

import psycopg2

from gamerbot.gamerbot import GamerBot

config = configparser.ConfigParser()
config.read('gamerbot.cfg')

try:
    connection = psycopg2.connect(user=config.get("PostgreSQL", "db_user"),
                                  password=config.get("PostgreSQL", "db_password"),
                                  host=config.get("PostgreSQL", "host"),
                                  port=config.get("PostgreSQL", "port"),
                                  database=config.get("PostgreSQL", "database"))

    phrases = config.get("Gamerbot", "phrases").split(',')

    token = config.get("Discord", "token")

    bot = GamerBot(connection, phrases)

    bot.run(token)

except Exception as e:
    import traceback
    traceback.print_exc()
