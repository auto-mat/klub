ALTER TABLE aklub_communication ADD COLUMN "type" VARCHAR(30);
UPDATE aklub_communication SET type='mass' where subject like 'PF 2011' or subject like 'Duben 2011';
UPDATE aklub_communication SET type='auto' where subject like 'Registrace podpory Auto*Matu' or subject like 'První upomínka opožděné pravidelné platby' or subject like 'Konečná upomínka neplatiče pravidelných plateb' or subject like 'Druhá jemná upomínka opožděné pravidelné platby';
UPDATE aklub_communication SET type='individual' where type is NULL;