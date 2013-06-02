
ALTER TABLE aklub_user ADD COLUMN "wished_tax_confirmation" boolean NOT NULL DEFAULT false;
ALTER TABLE aklub_user ADD COLUMN "wished_welcome_letter" boolean NOT NULL DEFAULT true;
ALTER TABLE aklub_user ALTER COLUMN wished_tax_confirmation SET DEFAULT true;
