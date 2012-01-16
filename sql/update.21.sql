alter table aklub_masscommunication add column "attach_tax_confirmation" boolean NOT NULL default false;
alter table aklub_taxconfirmation ADD CONSTRAINT user_year_key UNIQUE ("user_id", "year");