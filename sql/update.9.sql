CREATE TABLE "aklub_recruiter" (
    "id" serial NOT NULL PRIMARY KEY,
    "registered" date NOT NULL,
    "recruiter_id" integer CHECK ("recruiter_id" >= 0) NOT NULL,
    "firstname" varchar(40) NOT NULL,
    "surname" varchar(40) NOT NULL,
    "email" varchar(40) NOT NULL,
    "telephone" varchar(30) NOT NULL,
    "note" text NOT NULL
);

ALTER TABLE aklub_user ADD COLUMN "recruiter_id" integer REFERENCES "aklub_recruiter" ("id");
