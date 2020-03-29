CREATE TABLE "phrases" (
	"id" serial NOT NULL,
	"phrase" varchar(2000) NOT NULL UNIQUE,
	CONSTRAINT "phrases_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "phrase_fingerprint_bridge" (
	"phrase_id" integer NOT NULL,
	"fingerprint_id" integer NOT NULL,
	"location" integer NOT NULL
) WITH (
  OIDS=FALSE
);



CREATE TABLE "fingerprints" (
	"id" serial NOT NULL,
	"fingerprint" bigint NOT NULL UNIQUE,
	CONSTRAINT "fingerprints_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "users" (
	"uid" bigint NOT NULL,
	"user_name_id" integer NOT NULL
) WITH (
  OIDS=FALSE
);



CREATE TABLE "channels" (
	"uid" bigint NOT NULL,
	"guild_id" bigint NOT NULL,
	"channel_name_id" integer NOT NULL
) WITH (
  OIDS=FALSE
);



CREATE TABLE "guilds" (
	"uid" bigint NOT NULL,
	"guild_name_id" integer NOT NULL
) WITH (
  OIDS=FALSE
);



CREATE TABLE "channel_names" (
	"id" serial NOT NULL,
	"channel_name" varchar(100) NOT NULL,
	CONSTRAINT "channel_names_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "user_names" (
	"id" serial NOT NULL,
	"user_name" varchar(32) NOT NULL,
	CONSTRAINT "user_names_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "guild_names" (
	"id" serial NOT NULL,
	"guild_name" varchar(100) NOT NULL,
	CONSTRAINT "guild_names_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "messages" (
	"uid" bigint NOT NULL,
	"channel_id" bigint NOT NULL,
	"message_content_id" integer NOT NULL,
	"created_at" TIMESTAMP NOT NULL
) WITH (
  OIDS=FALSE
);



CREATE TABLE "message_content" (
	"id" serial NOT NULL,
	"content" varchar(2000) NOT NULL,
	CONSTRAINT "message_content_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "user_matched_phrases" (
	"id" serial NOT NULL,
	"phrase_id" integer NOT NULL,
	"user_id" bigint NOT NULL,
	"guild_id" bigint NOT NULL,
	"channel_id" bigint NOT NULL,
	"message_id" bigint NOT NULL,
	"matches" integer NOT NULL,
	CONSTRAINT "user_matched_phrases_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);




ALTER TABLE "phrase_fingerprint_bridge" ADD CONSTRAINT "phrase_fingerprint_bridge_fk0" FOREIGN KEY ("phrase_id") REFERENCES "phrases"("id");
ALTER TABLE "phrase_fingerprint_bridge" ADD CONSTRAINT "phrase_fingerprint_bridge_fk1" FOREIGN KEY ("fingerprint_id") REFERENCES "fingerprints"("id");


ALTER TABLE "users" ADD CONSTRAINT "users_fk0" FOREIGN KEY ("user_name_id") REFERENCES "user_names"("id");

ALTER TABLE "channels" ADD CONSTRAINT "channels_fk0" FOREIGN KEY ("guild_id") REFERENCES "guilds"("uid");
ALTER TABLE "channels" ADD CONSTRAINT "channels_fk1" FOREIGN KEY ("channel_name_id") REFERENCES "channel_names"("id");

ALTER TABLE "guilds" ADD CONSTRAINT "guilds_fk0" FOREIGN KEY ("guild_name_id") REFERENCES "guild_names"("id");




ALTER TABLE "messages" ADD CONSTRAINT "messages_fk0" FOREIGN KEY ("channel_id") REFERENCES "channels"("uid");
ALTER TABLE "messages" ADD CONSTRAINT "messages_fk1" FOREIGN KEY ("message_content_id") REFERENCES "message_content"("id");


ALTER TABLE "user_matched_phrases" ADD CONSTRAINT "user_matched_phrases_fk0" FOREIGN KEY ("phrase_id") REFERENCES "phrases"("id");
ALTER TABLE "user_matched_phrases" ADD CONSTRAINT "user_matched_phrases_fk1" FOREIGN KEY ("user_id") REFERENCES "users"("uid");
ALTER TABLE "user_matched_phrases" ADD CONSTRAINT "user_matched_phrases_fk2" FOREIGN KEY ("guild_id") REFERENCES "guilds"("uid");
ALTER TABLE "user_matched_phrases" ADD CONSTRAINT "user_matched_phrases_fk3" FOREIGN KEY ("channel_id") REFERENCES "channels"("uid");
ALTER TABLE "user_matched_phrases" ADD CONSTRAINT "user_matched_phrases_fk4" FOREIGN KEY ("message_id") REFERENCES "messages"("uid");



CREATE INDEX "idx_phrase" ON "phrases"("phrase");
CREATE INDEX "idx_fingerprint" ON "fingerprints"("fingerprint");
CREATE INDEX "idx_phrase_fingerprint_bridge_fingerprint_id" ON "phrase_fingerprint_bridge"("fingerprint_id");
CREATE INDEX "idx_phrase_fingerprint_bridge_phrase_id" ON "phrase_fingerprint_bridge"("phrase_id");

CREATE INDEX "idx_user_names" ON "user_names"("user_name");
CREATE INDEX "idx_user_uid" ON "users"("uid");

CREATE INDEX "idx_guild_names" ON "guild_names"("guild_name");
CREATE INDEX "idx_guild_uid" ON "guilds"("uid");

CREATE INDEX "idx_channel_names" ON "channel_names"("channel_name");
CREATE INDEX "idx_channels_uid" ON "channels"("uid");
CREATE INDEX "idx_channels_guild_id" ON "channels"("guild_id");

CREATE INDEX "idx_message_content" ON "message_content"("content");
CREATE INDEX "idx_messages_uid" ON "messages"("uid");
CREATE INDEX "idx_messages_channel_id" ON "message"("channel_id");
CREATE INDEX "idx_messages_created_at" ON "message"("created_at");

CREATE INDEX "idx_user_matched_phrases_phrase_id" ON "user_matched_phrases"("phrase_id");
CREATE INDEX "idx_user_matched_phrases_user_id" ON "user_matched_phrases"("user_id");
CREATE INDEX "idx_user_matched_phrases_guild_id" ON "user_matched_phrases"("guild_id");
CREATE INDEX "idx_user_matched_phrases_channel_id" ON "user_matched_phrases"("channel_id");