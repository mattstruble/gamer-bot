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

    def _ingest_user(self, db, user):
        user_name_id = ingest_if_not_exist_returning(db, USER_NAMES, {USER_NAMES.USER_NAME:user.name}, [USER_NAMES.ID])
        user_id = ingest_if_not_exist_returning(db, USERS, {USERS.UID:user.id, USERS.USER_NAME_ID: user_name_id}, [USERS.UID])

        return user_id

    def _ingest_guild(self, db, guild):
        guild_name_id = ingest_if_not_exist_returning(db, GUILD_NAMES, {GUILD_NAMES.GUILD_NAME:guild.name}, [GUILD_NAMES.ID])
        guild_id = ingest_if_not_exist_returning(db, GUILDS, {GUILDS.UID:guild.id, GUILDS.GUILD_NAME_ID:guild_name_id}, [GUILDS.UID])

        return guild_id

    def _ingest_channel(self, db, channel):
        channel_name_id = ingest_if_not_exist_returning(db, CHANNEL_NAMES, {CHANNEL_NAMES.CHANNEL_NAME:channel.name}, [CHANNEL_NAMES.ID])
        channel_id = ingest_if_not_exist_returning(db, CHANNELS, {CHANNELS.UID:channel.id, CHANNELS.GUILD_ID:channel.guild.id, CHANNELS.CHANNEL_NAME_ID:channel_name_id}, [CHANNELS.UID])

        return channel_id

    def _ingest_message(self, db, message):
        phrase_ids = self._get_matched_phrase_ids(message.content, db)

        # todo: user, guild, and channels should be ingested when bot joins guild not every message it receives
        user_id = self._ingest_user(db, message.author)
        guild_id = self._ingest_guild(db, message.guild)
        channel_id = self._ingest_channel(db, message.channel)

        message_content_id = ingest_if_not_exist_returning(db, MESSAGE_CONTENT, {MESSAGE_CONTENT.CONTENT:message.content}, [MESSAGE_CONTENT.ID])

        message_record = {
            MESSAGES.UID: message.id,
            MESSAGES.CHANNEL_ID: message.channel.id,
            MESSAGES.MESSAGE_CONTENT_ID: message_content_id,
            MESSAGES.CREATED_AT: message.created_at
        }

        message_id = ingest_if_not_exist_returning(db, MESSAGES, message_record, [MESSAGES.UID])

        if len(phrase_ids) > 0:

            prepared_log = db.insertInto(USER_MATCHED_PHRASES, USER_MATCHED_PHRASES.PHRASE_ID, USER_MATCHED_PHRASES.USER_ID,
                                         USER_MATCHED_PHRASES.GUILD_ID, USER_MATCHED_PHRASES.CHANNEL_ID, USER_MATCHED_PHRASES.MESSAGE_ID,
                                         USER_MATCHED_PHRASES.MATCHES)

            for phrase_id in phrase_ids:
                # todo: replace matches with count of matches in message
                prepared_log = prepared_log.prepare(phrase_id, user_id, guild_id, channel_id, message_id, 1)

            prepared_log.execute()
            self.db_connection.commit()

    async def on_message(self, message):
        if message.author == self.user:
            return

        db = Database(self.db_connection)
        self._ingest_message(db, message)
