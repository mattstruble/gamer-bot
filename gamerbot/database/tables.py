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
    columns = ["uid", "guild_id", "channel_name_id"]
    non_pk_columns = columns[1:]

    UID = "uid"
    GUILD_ID = "guild_id"
    CHANNEL_NAME_ID = "channel_name_id"


class CHANNEL_NAMES(_TABLE):
    name = "channel_names"
    columns = ["id", "channel_name"]
    non_pk_columns = columns[1:]

    ID = "id"
    CHANNEL_NAME = "channel_name"


class GUILDS(_TABLE):
    name = "guilds"
    columns = ["uid", "guild_name_id"]
    non_pk_columns = columns[1:]

    UID = "uid"
    GUILD_NAME_ID = "guild_name_id"


class GUILD_NAMES(_TABLE):
    name = "guild_names"
    columns = ["id", "guild_name"]
    non_pk_columns = columns[1:]

    ID = "id"
    GUILD_NAME = "guild_name"


class MESSAGES(_TABLE):
    name = "messages"
    columns = ["uid", "user_id", "channel_id", "message_content_id", "created_at"]
    non_pk_columns = columns[1:]

    UID = "uid"
    USER_ID = "user_id"
    CHANNEL_ID = "channel_id"
    MESSAGE_CONTENT_ID = "message_content_id"
    CREATED_AT = "created_at"


class MESSAGE_CONTENT(_TABLE):
    name = "message_content"
    columns = ["id", "content"]
    non_pk_columns = columns[1:]

    ID = "id"
    CONTENT= "content"


class PHRASES(_TABLE):
    name = "phrases"
    columns = ["id", "phrase"]
    non_pk_columns = columns[1:]

    ID = "id"
    PHRASE = "phrase"


class USERS(_TABLE):
    name = "users"
    columns = ["uid", "user_name_id"]
    non_pk_columns = columns[1:]

    UID = "uid"
    USER_NAME_ID = "user_name_id"


class USER_NAMES(_TABLE):
    name = "user_names"
    columns = ["id", "user_name"]
    non_pk_columns = columns[1:]

    ID = "id"
    USER_NAME = "user_name"


class USER_MATCHED_PHRASES(_TABLE):
    name = "user_matched_phrases"
    columns = ["id", "phrase_id", "user_id", "guild_id", "channel_id", "message_id", "matches"]
    non_pk_columns = columns[1:]

    ID = "id"
    PHRASE_ID = "phrase_id"
    USER_ID = "user_id"
    GUILD_ID = "guild_id"
    CHANNEL_ID = "channel_id"
    MESSAGE_ID = "message_id"
    MATCHES = "matches"
