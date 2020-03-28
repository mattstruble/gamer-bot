#!/usr/bin/env python

# Copyright (c) 2020 Matt Struble. All Rights Reserved.
#
# Use is subject to license terms.
#
# Author: Matt Struble
# Date: Mar. 27 2020


class _TABLE(object):
    name = "TABLE"
    columns = []
    non_pk_columns = []


class CHANNELS(_TABLE):
    name = "channels"
    columns = ["id", "channel", "guild_id"]
    non_pk_columns = columns[1:]

    ID = "id"
    CHANNEL = "channel"
    GUILD_ID = "guild_id"


class FINGERPRINTS(_TABLE):
    name = "fingerprints"
    columns = ["id", "fingerprint"]
    non_pk_columns = columns[1:]

    ID = "id"
    FINGERPRINT = "fingerprint"


class GUILDS(_TABLE):
    name = "guilds"
    columns = ["id", "guild"]
    non_pk_columns = columns[1:]

    ID = "id"
    GUILD = "guild"


class LOGS(_TABLE):
    name = "logs"
    columns = ["id", "phrase_id", "user_id", "channel_id", "message_id", "reported"]
    non_pk_columns = columns[1:]

    ID = "id"
    PHRASE_ID = "phrase_id"
    USER_ID = "user_id"
    CHANNEL_ID = "channel_id"
    MESSAGE_ID = "message_id"
    REPORTED = "reported"


class MESSAGES(_TABLE):
    name = "messages"
    columns = ["id", "message"]
    non_pk_columns = columns[1:]

    ID = "id"
    MESSAGE = "message"

class PHRASES(_TABLE):
    name = "phrases"
    columns = ["id", "phrase"]
    non_pk_columns = columns[1:]

    ID = "id"
    PHRASE = "phrase"


class PHRASE_FINGERPRINT_BRIDGE(_TABLE):
    name = "phrase_fingerprint_bridge"
    columns = ["phrase_id", "fingerprint_id", "location"]
    non_pk_columns = columns

    PHRASE_ID = "phrase_id"
    FINGERPRINT_ID = "fingerprint_id"
    LOCATION = "location"


class USERS(_TABLE):
    name = "users"
    columns = ["id", "user"]
    non_pk_columns = columns[1:]

    ID = "id"
    USER = "user"