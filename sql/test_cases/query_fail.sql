-- get invoice that does not exist (fail)
INSERT INTO member_pays_invoice (invoice_id, member_id)
VALUES (999, 1);
