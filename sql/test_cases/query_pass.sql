-- get invoice for member (pass)
SELECT m.username, i.status, i.amount_due
FROM member_pays_invoice mpi
JOIN members m ON m.member_id = mpi.member_id
JOIN invoice i ON i.invoice_id = mpi.invoice_id
WHERE mpi.member_id = 1 AND mpi.invoice_id = 1;