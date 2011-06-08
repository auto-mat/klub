
CREATE TABLE "aklub_campaign" (
    "id" serial NOT NULL PRIMARY KEY,
    "created" date NOT NULL,
    "name" varchar(50) NOT NULL,
    "description" text NOT NULL
)
;
CREATE TABLE "aklub_user_campaigns" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL,
    "campaign_id" integer NOT NULL REFERENCES "aklub_campaign" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("user_id", "campaign_id")
)


