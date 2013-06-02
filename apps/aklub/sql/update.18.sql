ALTER TABLE "aklub_user" ADD COLUMN "verified" boolean;
ALTER TABLE "aklub_user" ADD COLUMN "verified_by_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "aklub_user_verified_by_id" ON "aklub_user" ("verified_by_id");
UPDATE aklub_user set verified=True;
update aklub_user set verified=false where addressment='';
ALTER TABLE "aklub_user" ALTER COLUMN "verified" SET NOT NULL:
