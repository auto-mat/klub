ALTER TABLE aklub_user RENAME COLUMN monthly_payment TO regular_amount;
ALTER TABLE aklub_user ADD COLUMN regular_frequency varchar(20);


