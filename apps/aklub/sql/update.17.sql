ALTER TABLE aklub_masscommunication DROP COLUMN dispatch_auto;
ALTER TABLE aklub_masscommunication ADD COLUMN send boolean NOT NULL DEFAULT false;