ALTER TABLE aklub_communication ADD COLUMN "created_by_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
UPDATE aklub_communication SET created_by_id=handled_by_id;
UPDATE aklub_communication SET handled_by_id=NULL;
