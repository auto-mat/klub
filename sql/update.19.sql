alter table aklub_masscommunication add column "template_en" text;
alter table aklub_masscommunication add column "date" date;
update aklub_user set language='en' where language='english';
update aklub_user set language='cs' where language='czech';
alter table aklub_masscommunication alter column template drop not null;
