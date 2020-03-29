import datetime

import discord

from .database.conditionals import In, Eq
from .database.database import Database
from .database.functions import ingest_if_not_exist_returning, ingest_if_not_exist
from .database.ordering import Asc
from .database.tables import *
from .util.fingerprint import Fingerprint


class GamerBot(discord.AutoShardedClient):

    def __init__(self, connection, phrases, loop=None, **options):
        super().__init__(loop=loop, options=options)

        min_str_len = len(min(phrases, key=len))

        self.fingerprint = Fingerprint(kgram_len=int(min_str_len/2), window_len=int(min_str_len/2))

        self.db_connection = connection
        self._ingest_phrases(phrases)
        self.percent_match = .8



    def _ingest_phrases(self, phrases):
        db = Database(self.db_connection)

        for phrase in phrases:
            phrase_id = ingest_if_not_exist_returning(db, PHRASES, {PHRASES.PHRASE:phrase}, [PHRASES.ID])

            fingerprints = self.fingerprint.generate(phrase)

            for fingerprint, location in fingerprints:
                fingerprint_id = ingest_if_not_exist_returning(db, FINGERPRINTS, {FINGERPRINTS.FINGERPRINT: fingerprint}, [FINGERPRINTS.ID])

                phrase_bridge_record = {PHRASE_FINGERPRINT_BRIDGE.PHRASE_ID: phrase_id,
                                        PHRASE_FINGERPRINT_BRIDGE.FINGERPRINT_ID: fingerprint_id,
                                        PHRASE_FINGERPRINT_BRIDGE.LOCATION: location}

                ingest_if_not_exist(db, PHRASE_FINGERPRINT_BRIDGE, phrase_bridge_record)

        self.db_connection.commit()

    def _get_matched_phrase_ids(self, message, db):
        phrases = db.selectFrom(PHRASES).fetchall()

        matched = []

        for phrase_dict in phrases:
            phrase_id = phrase_dict[PHRASES.ID]
            phrase = phrase_dict[PHRASES.PHRASE]

            if phrase in message:
                matched.append(phrase_id)
            else:
                fingerprints = [x[0] for x in self.fingerprint.generate(message)]

                message_fingerprints_ids = db.select(FINGERPRINTS.ID).FROM(FINGERPRINTS) \
                    .WHERE(In(FINGERPRINTS.FINGERPRINT, fingerprints)).fetchall()

                phrase_fingerprints_ids = db.select(PHRASE_FINGERPRINT_BRIDGE.FINGERPRINT_ID).FROM(PHRASE_FINGERPRINT_BRIDGE) \
                    .WHERE(Eq(PHRASE_FINGERPRINT_BRIDGE.PHRASE_ID, phrase_id)) \
                    .orderBy((PHRASE_FINGERPRINT_BRIDGE.LOCATION, Asc)).fetchall()

                matching = set(message_fingerprints_ids) & set(phrase_fingerprints_ids)

                if len(matching) > len(phrase_fingerprints_ids) * self.percent_match:
                    matched.append(phrase_id)

        return matched

    def _ingest_message(self, db, message):
        phrase_ids = self._get_matched_phrase_ids(message.content, db)

        if len(phrase_ids) > 0:
            prepared_log = db.insertInto(LOGS, LOGS.PHRASE_ID, LOGS.USER_ID, LOGS.CHANNEL_ID, LOGS.MESSAGE_ID,
                                         LOGS.REPORTED)

            user_id = ingest_if_not_exist_returning(db, USERS, {USERS.USER: message.author.name}, [USERS.ID])
            guild_id = ingest_if_not_exist_returning(db, GUILDS, {GUILDS.GUILD: message.guild.name}, [GUILDS.ID])
            channel_id = ingest_if_not_exist_returning(db, CHANNELS, {CHANNELS.CHANNEL: message.channel.name,
                                                                      CHANNELS.GUILD_ID: guild_id}, [CHANNELS.ID])
            message_id = ingest_if_not_exist_returning(db, MESSAGES, {MESSAGES.MESSAGE: message.content}, [MESSAGES.ID])

            reported = datetime.datetime.now()

            for phrase_id in phrase_ids:
                prepared_log = prepared_log.prepare(phrase_id, user_id, channel_id, message_id, reported)

            prepared_log.execute()
            self.db_connection.commit()

    async def on_message(self, message):
        if message.author == self.user:
            return

        db = Database(self.db_connection)
        self._ingest_message(db, message)
