import discord

from .database.conditionals import Eq
from .database.database import Database, Sum
from .database.functions import ingest_if_not_exist_returning, fetchone_from_table
from .database.ordering import Desc
from .database.tables import *
from .util.fingerprint import Fingerprint, template_match_fingerprints


class GamerBot(discord.AutoShardedClient):

    command_trigger = "gs!"
    help_trigger = "!help"

    commands = {
        "": {'msg': "Display the overall stats for the server.", 'super': False},
        "user": {'msg': "Display the stats for mentioned users.", 'super': False},
        "channel": {'msg': "Display the stats for the current channel.", 'super': False},
        "list": {'msg': "List the phrases the bot is tracking.", 'super': False},
        "add": {'msg': "Adds anything trailing the command as a single phrase to be counted. _Superusers only._", 'super': True},
        "remove": {'msg': "Enter an identification number of a phrase to remove, can be found using gs!list. _Superusers only._", 'super': True},
        "recount": {'msg': "Recounts all the messages in the guild, automatically triggered when add or remove are called. _Superusers only._", 'super': True},
        "help": {'msg': "Display help", 'super': False}
    }

    def __init__(self, connection, phrases, loop=None, **options):
        super().__init__(loop=loop, options=options)
        self.phrase_dict = {}
        self.percent_match = .9

        self.fingerprint = Fingerprint()

        self.db_connection = connection
        self._ingest_phrases(phrases)


    def _ingest_phrases(self, phrases):
        db = Database(self.db_connection)

        for phrase in phrases:
            phrase_id = ingest_if_not_exist_returning(db, PHRASES, {PHRASES.PHRASE:phrase.lower()}, [PHRASES.ID])
            self.phrase_dict[phrase_id] = phrase

        self.db_connection.commit()

    def _get_matched_phrase_ids(self, content, db):
        content = content.lower()

        phrases = db.selectFrom(PHRASES).fetchall()

        matched = {}

        for phrase_dict in phrases:
            phrase_id = phrase_dict[PHRASES.ID]
            phrase = phrase_dict[PHRASES.PHRASE]

            # single word phrases look for a direct match
            if len(phrase.split(" ")) == 1:
                count = content.count(phrase)
                if count > 0:
                    matched[phrase_id] = count
            else: # else perform template matching
                try :
                    fingerprinter = self.fingerprint.get_fingerprinter_from_string(phrase)

                    content_fingerprints = fingerprinter.generate(content)
                    template_fingerprints = fingerprinter.generate(phrase)

                    if len(content_fingerprints) == 0 or len(template_fingerprints) == 0:
                        continue

                    template_matches = template_match_fingerprints(template_fingerprints, content_fingerprints)

                    if len(template_matches) > 0:
                        matched[phrase_id] = len(template_matches)
                except:
                    pass

        return matched

    def _ingest_message(self, db, message):
        if message.author == self.user:
            return

        matched_count = self._get_matched_phrase_ids(message.content, db)

        message_content_id = ingest_if_not_exist_returning(db, MESSAGE_CONTENT, {MESSAGE_CONTENT.CONTENT:message.content}, [MESSAGE_CONTENT.ID])

        message_record = {
            MESSAGES.UID: message.id,
            MESSAGES.USER_ID: message.author.id,
            MESSAGES.CHANNEL_ID: message.channel.id,
            MESSAGES.MESSAGE_CONTENT_ID: message_content_id,
            MESSAGES.CREATED_AT: message.created_at
        }

        message_id = ingest_if_not_exist_returning(db, MESSAGES, message_record, [MESSAGES.UID])

        if matched_count is not None and len(matched_count) > 0:
            prepared_log = db.insertInto(USER_MATCHED_PHRASES, USER_MATCHED_PHRASES.PHRASE_ID, USER_MATCHED_PHRASES.USER_ID,
                                         USER_MATCHED_PHRASES.GUILD_ID, USER_MATCHED_PHRASES.CHANNEL_ID, USER_MATCHED_PHRASES.MESSAGE_ID,
                                         USER_MATCHED_PHRASES.MATCHES)

            for phrase_id in matched_count.keys():
                if matched_count[phrase_id] > 0: # only ingest row if it has matches
                    prepared_log = prepared_log.prepare(phrase_id, message.author.id, message.guild.id, message.channel.id, message_id, matched_count[phrase_id])

            prepared_log.execute()

    def _get_help(self):
        message = ""

        for key, value in self.commands.items():
            message += "`{}{}`: {}\n".format(self.command_trigger, key, value['msg'])

        return message

    def _get_phrase(self, db, phrase_id):
        return self.phrase_dict[phrase_id] #db.select(PHRASES.PHRASE).FROM(PHRASES).WHERE(Eq(PHRASES.ID, phrase_id)).LIMIT(1).fetchone

    def _get_stats(self, db, conditional, location_str, no_match_string):
        top_user_row = db.select(USER_MATCHED_PHRASES.USER_ID, Sum(USER_MATCHED_PHRASES.MATCHES)).FROM(
            USER_MATCHED_PHRASES) \
            .WHERE(conditional) \
            .groupBy(USER_MATCHED_PHRASES.USER_ID).orderBy(("sum", Desc)).LIMIT(3).fetchmany(3)

        if top_user_row is None:
            return no_match_string

        top_user = self.get_user(top_user_row[0][USER_MATCHED_PHRASES.USER_ID])

        message = "The top GAMER of this {} is {} with a total count of: **{}**\n\n".format(location_str, top_user.mention,
                                                                                            top_user_row[0]['sum'])

        for stat in top_user_row:
            message += "{}: **{}**".format(self.get_user(stat[USER_MATCHED_PHRASES.USER_ID]).mention, stat['sum'])
            message += self._get_user_stats(db, stat[USER_MATCHED_PHRASES.USER_ID], conditional)
            message += "\n\n"

        return message

    def _get_guild_stats(self, db, guild_id):
        return self._get_stats(db, Eq(USER_MATCHED_PHRASES.GUILD_ID, guild_id), "sever", "Couldn't find any GAMERS in this guild.")

    def _get_channel_stats(self, db, channel_id):
        return self._get_stats(db, Eq(USER_MATCHED_PHRASES.CHANNEL_ID, channel_id), "channel", "Couldn't find any GAMERS in this channel.")

    def _get_user_stats(self, db, user_id, conditional):
        message = ""

        breakdown_ret = db.select(USER_MATCHED_PHRASES.USER_ID, USER_MATCHED_PHRASES.PHRASE_ID,
                                  Sum(USER_MATCHED_PHRASES.MATCHES)) \
            .FROM(USER_MATCHED_PHRASES).WHERE(conditional) \
            .AND(Eq(USER_MATCHED_PHRASES.USER_ID, user_id)) \
            .groupBy(USER_MATCHED_PHRASES.USER_ID, USER_MATCHED_PHRASES.PHRASE_ID) \
            .orderBy(("sum", Desc)).LIMIT(3).fetchmany(3)

        for i, stat in enumerate(breakdown_ret):
            phrase = self._get_phrase(db, stat[USER_MATCHED_PHRASES.PHRASE_ID])
            count = stat['sum']
            message += "\n{}. `{}`: {}".format(i + 1, phrase, count)

        return message

    def _get_users_stats(self, db, user_ids):
        message = ""

        if len(user_ids) == 0:
            return self._get_help()

        for user_id in user_ids:
            user = self.get_user(user_id)

            total_row = db.select(USER_MATCHED_PHRASES.USER_ID, Sum(USER_MATCHED_PHRASES.MATCHES)).FROM(
                USER_MATCHED_PHRASES) \
                .WHERE(Eq(USER_MATCHED_PHRASES.USER_ID, user_id)) \
                .groupBy(USER_MATCHED_PHRASES.USER_ID).orderBy(("sum", Desc)).LIMIT(1).fetchone()

            if total_row is None:
                message += "{} hasn't said any GAMER words.\n\n".format(user.mention)
            else:
                message += "{}: **{}**".format(user.mention, total_row['sum'])
                message += self._get_user_stats(db, user_id, Eq(USER_MATCHED_PHRASES.USER_ID, user_id))

                message += "\n\n"

        return message


    async def _handle_commands(self, db, message):
        command = message.content.split('!')[1].split(' ')[0]

        if command == "":
            print_message = self._get_guild_stats(db, message.guild.id)
        elif command == "user":
            print_message = self._get_users_stats(db, message.raw_mentions)
        elif command == "channel":
            print_message = self._get_channel_stats(db, message.channel.id)
        else:
            print_message = self._get_help()

        await message.channel.send(print_message)

    @staticmethod
    def _ingest_name_lookup_table(db, table, uid_column, uid_value, name_id_column, name_id_value):
        uid_row = fetchone_from_table(db, table, {uid_column:uid_value}, table.columns)
        ret_id = uid_value

        if uid_row is not None and uid_row[name_id_column] != name_id_value:
            db.update(table).set(name_id_column, name_id_value).WHERE(Eq(uid_column, uid_value)).execute()
        elif uid_row is None:
            ret_id = ingest_if_not_exist_returning(db, table, {uid_column:uid_value, name_id_column:name_id_value}, [uid_column])

        return ret_id

    @staticmethod
    def _ingest_user(db, user):
        user_name_id = ingest_if_not_exist_returning(db, USER_NAMES, {USER_NAMES.USER_NAME:user.name}, [USER_NAMES.ID])

        user_id = GamerBot._ingest_name_lookup_table(db, USERS, USERS.UID, user.id, USERS.USER_NAME_ID, user_name_id)

        return user_id

    @staticmethod
    def _ingest_guild(db, guild):
        guild_name_id = ingest_if_not_exist_returning(db, GUILD_NAMES, {GUILD_NAMES.GUILD_NAME:guild.name}, [GUILD_NAMES.ID])

        guild_id = GamerBot._ingest_name_lookup_table(db, GUILDS, GUILDS.UID, guild.id, GUILDS.GUILD_NAME_ID, guild_name_id)

        return guild_id

    @staticmethod
    def _ingest_channel(db, channel):
        if isinstance(channel, discord.TextChannel): # only care about text channels
            channel_name_id = ingest_if_not_exist_returning(db, CHANNEL_NAMES, {CHANNEL_NAMES.CHANNEL_NAME:channel.name}, [CHANNEL_NAMES.ID])

            channel_id = GamerBot._ingest_name_lookup_table(db, CHANNELS, CHANNELS.UID, channel.id, CHANNELS.CHANNEL_NAME_ID,  channel_name_id)

            return channel_id
        else:
            return None

    @staticmethod
    def _is_command_message(message):
        return message.content.startswith(GamerBot.command_trigger) or message.content.startswith(GamerBot.help_trigger)

    async def _ingest_channel_history(self, db, channel):
        if not isinstance(channel, discord.TextChannel):
            return

        last_message_time = db.select(MESSAGES.CREATED_AT).FROM(MESSAGES).WHERE(Eq(MESSAGES.CHANNEL_ID, channel.id))\
            .orderBy((MESSAGES.CREATED_AT, Desc)).LIMIT(1).fetchone()

        for message in await channel.history(limit=None, after=last_message_time, oldest_first=True).flatten(): # iterate over all channel history from last message
            if not self._is_command_message(message):
                self._ingest_message(db, message)

    async def on_ready(self):
        db = Database(self.db_connection)

        for guild in self.guilds:
            await self.on_guild_join(guild)

        # for channel in self.get_all_channels():
        #     await self._ingest_channel_history(db, channel)

        db.commit()

    async def on_message(self, message):
        if message.author == self.user:
            return

        db = Database(self.db_connection)

        if self._is_command_message(message):
            await self._handle_commands(db, message)
        else:
            self._ingest_message(db, message)

        db.commit()

    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            db = Database(self.db_connection)

            new_name_id = ingest_if_not_exist_returning(db, CHANNEL_NAMES, {CHANNEL_NAMES.CHANNEL_NAME:after.name}, [CHANNEL_NAMES.ID])
            db.update(CHANNELS).set(CHANNELS.CHANNEL_NAME_ID, new_name_id).WHERE(Eq(CHANNELS.UID, before.id)).execute()

    async def on_guild_channel_create(self, channel):
        db = Database(self.db_connection)
        self._ingest_channel(db, channel)

        db.commit()

    async def on_member_join(self, member):
        db = Database(self.db_connection)
        self._ingest_user(db, member)

        db.commit()

    async def on_guild_update(self, before, after):
        if before.name != after.name:
            db = Database(self.db_connection)

            new_name_id = ingest_if_not_exist_returning(db, GUILD_NAMES, {GUILD_NAMES.GUILD_NAME:after.name}, [GUILD_NAMES.ID])
            db.update(GUILDS).set(GUILDS.GUILD_NAME_ID, new_name_id).WHERE(Eq(GUILDS.UID, before.id)).execute()

    async def on_guild_join(self, guild):
        db = Database(self.db_connection)
        self._ingest_guild(db, guild)

        for user in guild.members:
            self._ingest_user(db, user)

        for channel in guild.text_channels:
            self._ingest_channel(db, channel)

        db.commit()

        # split history ingestion from normal channel ingestion for efficiency. Want channels in first to allow processing
        # of messages as they come in
        for channel in guild.text_channels:
            await self._ingest_channel_history(db, channel)

        db.commit()
