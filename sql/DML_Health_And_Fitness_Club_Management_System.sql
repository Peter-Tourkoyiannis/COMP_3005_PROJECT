-- Main Tables

INSERT INTO users (email, first_name, last_name)
VALUES 	('peter.tourkoyiannis@cu.com', 'Peter', 'Tourkoyiannis'),
		('aryan.patel@cu.com', 'Aryan', 'Patel'),
		('ethan.letto@cu.com', 'Ethan', 'Letto')
;

INSERT INTO trainer (biography, certifications, user_id)
VALUES 	('Experienced sitting in penalty box.', 'CS', 3)
;

INSERT INTO members (date_of_birth, gender, username, user_password, user_id)
VALUES 	(20040101, 'M', 'arypat', 'hockey', 2)
;

INSERT INTO admin_staff (user_id)
VALUES 	(1)
;

INSERT INTO admin_system (admin_id)
VALUES 	(1)
;

INSERT INTO equipment (operational_status, maintenance_status, maintenance_records, equipment_type)
VALUES 	(true, 'Good', 'No issues', 'Bench Press')
;

INSERT INTO schedule (type_of)
VALUES 	('Hockey Skills 101')
;

INSERT INTO training_session (availability, session_notes, start_time, duration, schedule_id)
VALUES 	(true, 'Learn To Shoot', 900, 60, 1)
;

INSERT INTO room_booking (room_number, room_type, schedule_id, session_id)
VALUES 	(101, 'Weight Room', 1, 1)
;

INSERT INTO invoice (status, due_date, amount_due)
VALUES 	('Unpaid', 20251016, 70)
;

INSERT INTO work_schedule (hours_per_week, availability_periods, working_periods, trainer_id)
VALUES 	(44, 'Mon-Thu, Sat', 'Mon, Tues, Sat', 1)
;

INSERT INTO fitness_goals (goal_type, target, start_date, end_date, member_id)
VALUES 	('Weight Gain', 'Gain 12kg', 20250101, 20260101, 1)
;

INSERT INTO health_metrics (metric_type, unit, recorded_date, member_id)
VALUES 	('72.5', 'kg', 20251128, 1)
;

INSERT INTO session_registration (class_attendance)
VALUES 	('Peter Tourkoyiannis')
;

-- NOTE: I made it both types of class for testing

INSERT INTO group_class (capacity, session_id)
VALUES  (20, 1)
;

INSERT INTO personal_training_session (session_id)
VALUES  (1)
;

-- 1:N Tables

INSERT INTO admin_manage_schedule (admin_id, schedule_id)
VALUES 	(1, 1)
;

INSERT INTO admin_access_work_schedule (admin_id, trainer_schedule_id)
VALUES 	(1, 1)
;

INSERT INTO admin_manages_equipment (equipment_id, admin_id)
VALUES  (1, 1)
;

INSERT INTO room_booking_has_equipment (equipment_id, room_id)
VALUES 	(1, 1)
;

INSERT INTO admin_system_accesses_members (member_id, system_id)
VALUES 	(1, 1)
;

INSERT INTO member_pays_invoice (invoice_id, member_id)
VALUES 	(1, 1)
;

INSERT INTO admin_system_generates_invoice (system_id, invoice_id)
VALUES 	(1, 1)
;

INSERT INTO trainer_reviews_training_session (session_id, trainer_id)
VALUES 	(1, 1)
;

INSERT INTO trainer_views_members (trainer_id, member_id)
VALUES 	(1, 1)
;

INSERT INTO group_class_has_session_registration (registration_id, class_id)
VALUES 	(1, 1)
;

INSERT INTO personal_training_session_has_session_registration (registration_id, pt_id)
VALUES  (1, 1)
;

INSERT INTO member_manages_session_registration (registration_id, member_id)
VALUES (1, 1);
