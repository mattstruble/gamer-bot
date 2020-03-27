CREATE TABLE "guilds" (
	"id" serial NOT NULL,
	"guild" varchar(100) NOT NULL,
	CONSTRAINT "guilds_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "channels" (
	"id" serial NOT NULL,
	"guild_id" integer NOT NULL,
	"channel" varchar(100) NOT NULL,
	CONSTRAINT "channels_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "users" (
	"id" serial NOT NULL,
	"user" varchar(32) NOT NULL,
	CONSTRAINT "users_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "phrases" (
	"id" serial NOT NULL,
	"phrase" varchar(2000) NOT NULL,
	CONSTRAINT "phrases_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "fingerprints" (
	"id" serial NOT NULL,
	"fingerprint" bigint NOT NULL,
	CONSTRAINT "fingerprints_pk" PRIMARY KEY ("id")
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



CREATE TABLE "logs" (
	"id" serial NOT NULL,
	"phrase_id" integer NOT NULL,
	"user_id" integer NOT NULL,
	"channel_id" integer NOT NULL,
	"message_id" integer NOT NULL,
	"reported" TIMESTAMP NOT NULL,
	CONSTRAINT "logs_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "messages" (
	"id" serial NOT NULL,
	"message" varchar(2000) NOT NULL,
	CONSTRAINT "messages_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);




ALTER TABLE "channels" ADD CONSTRAINT "channels_fk0" FOREIGN KEY ("guild_id") REFERENCES "guilds"("id");

ALTER TABLE "phrase_fingerprint_bridge" ADD CONSTRAINT "phrase_fingerprint_bridge_fk0" FOREIGN KEY ("phrase_id") REFERENCES "phrases"("id");
ALTER TABLE "phrase_fingerprint_bridge" ADD CONSTRAINT "phrase_fingerprint_bridge_fk1" FOREIGN KEY ("fingerprint_id") REFERENCES "fingerprints"("id");

ALTER TABLE "logs" ADD CONSTRAINT "logs_fk0" FOREIGN KEY ("phrase_id") REFERENCES "phrases"("id");
ALTER TABLE "logs" ADD CONSTRAINT "logs_fk1" FOREIGN KEY ("user_id") REFERENCES "users"("id");
ALTER TABLE "logs" ADD CONSTRAINT "logs_fk2" FOREIGN KEY ("channel_id") REFERENCES "channels"("id");
ALTER TABLE "logs" ADD CONSTRAINT "logs_fk3" FOREIGN KEY ("message_id") REFERENCES "messages"("id");

CREATE INDEX "idx_phrase" ON "phrases"("phrase");
CREATE INDEX "idx_user" ON "users"("user");
CREATE INDEX "idx_channel" ON "channels"("channel");
CREATE INDEX "idx_guild" ON "guilds"("guild");
CREATE INDEX "idx_message" ON "messages"("message");
CREATE INDEX "idx_fingerprint" ON "fingerprints"("fingerprint");
CREATE INDEX "idx_phrase_fingerprint_bridge_fingerprint_id" ON "phrase_fingerprint_bridge"("fingerprint_id");
CREATE INDEX "idx_logs_phrase_id" ON "logs"("phrase_id");
CREATE INDEX "idx_logs_user_id" ON "logs"("user_id");
CREATE INDEX "idx_logs_channel_id" ON "logs"("channel_id");