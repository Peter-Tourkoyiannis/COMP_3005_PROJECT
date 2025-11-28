-- Main tables that hold data

create table users
	(user_id	serial,
	email		varchar(255) 	not null unique,
	first_name	varchar(30) 	not null,
	last_name	varchar(30)	 	not null,
	primary key (user_id)
	);

create table trainer
	(trainer_id		serial,
	biography		text,
	certifications	text,
	user_id			integer,
	primary key (trainer_id),
	foreign key (user_id) references users
	);

create table members
	(member_id		serial,
	date_of_birth	integer 	not null,
	gender			varchar(1),
	username		varchar(30) not null unique,
	user_password	varchar(30) not null,
	user_id			integer,
	primary key (member_id),
	foreign key (user_id) 	references users
	);

create table admin_staff
	(admin_id 	serial,
	user_id		integer,
	primary key (admin_id),
	foreign key (user_id) references users
	);

create table admin_system
	(system_id	serial,
	admin_id	integer,
	primary key	(system_id),
	foreign key (admin_id) references admin_staff
	);

create table equipment 
	(equipment_id		serial,
	operational_status	bool,
	maintenance_status	varchar(30),
	maintenance_records	text,
	equipment_type		varchar(30),
	primary key (equipment_id)
	);

create table schedule
	(schedule_id	serial,
	type_of			varchar(255),
	primary key (schedule_id)
	);

create table training_session
	(session_id		serial,
	availability	bool,
	session_notes	text,
	start_time		integer,
	duration		integer,
	schedule_id		integer,
	primary key (session_id),
	foreign key (schedule_id) references schedule
	);

create table room_booking
	(room_id	serial,
	room_number	integer,
	room_type	varchar(255),
	schedule_id	integer,
	session_id	integer,
	primary key (room_id),
	foreign key (schedule_id) references schedule,
	foreign key (session_id) references training_session
	);

create table invoice
	(invoice_id	serial,
	status		varchar(30),
	due_date	integer,
	amount_due	integer,
	primary key (invoice_id)
	);

create table work_schedule
	(trainer_schedule_id	serial,
	hours_per_week			int,
	availability_periods	text,
	working_periods			text,
	trainer_id				integer,
	primary key (trainer_schedule_id),
	foreign key (trainer_id) 	references trainer
	);

create table fitness_goals
	(goal_id	serial,
	goal_type	text,
	target		text,
	start_date	integer,
	end_date	integer,
	member_id	integer,
	primary key (goal_id),
	foreign key (member_id) references members
	);

create table health_metrics
	(metric_id		serial,
	metric_type		text,
	unit			varchar(20),
	recorded_date	integer,
	member_id		integer,
	primary key (metric_id),
	foreign key (member_id) references members
	);

create table session_registration
	(registration_id	serial,
	class_attendance	text,
	primary key (registration_id)	
	);

create table group_class
	(class_id	serial,
	capacity	integer,
	session_id	integer,
	primary key (class_id),
	foreign key (session_id) references training_session
	);

create table personal_training_session
	(pt_id	serial,
	session_id	integer,
	primary key (pt_id),
	foreign key (session_id) references training_session
	);

-- Tables that link 1:N tables together

create table admin_manage_schedule
	(admin_id		integer,
	schedule_id		integer,
	primary key (admin_id, schedule_id),
	foreign key (admin_id) 		references admin_staff,
	foreign key (schedule_id) 	references schedule
	);

create table admin_access_work_schedule
	(admin_id			integer,
	trainer_schedule_id	integer,
	primary key (admin_id, trainer_schedule_id),
	foreign key (admin_id) 				references admin_staff,
	foreign key (trainer_schedule_id) 	references work_schedule
	);

create table admin_manages_equipment
	(equipment_id	integer,
	admin_id		integer,
	primary key (equipment_id, admin_id),
	foreign key (admin_id) 		references admin_staff,
	foreign key (equipment_id) 	references equipment	
	);

create table room_booking_has_equipment
	(equipment_id	integer,
	room_id			integer,
	primary key (equipment_id, room_id),
	foreign key (room_id) 		references room_booking,
	foreign key (equipment_id) 	references equipment	
	);

create table admin_system_accesses_members
	(member_id	integer,
	system_id	integer,
	primary key (member_id, system_id),
	foreign key (system_id) references admin_system,
	foreign key (member_id) references members	
	);

create table member_pays_invoice
	(invoice_id integer,
	member_id	integer,
	primary key (member_id, invoice_id),
	foreign key (invoice_id) references invoice,
	foreign key (member_id) references members
	);

create table admin_system_generates_invoice
	(system_id	integer,
	invoice_id	integer,
	primary key (system_id, invoice_id),
	foreign key (system_id) references admin_system,
	foreign key (invoice_id) references invoice
	);

create table trainer_reviews_training_session
	(session_id	integer,
	trainer_id	integer,
	primary key (session_id, trainer_id),
	foreign key (trainer_id) references	trainer,
	foreign key (session_id) references training_session
	);

create table trainer_views_members
	(trainer_id	integer,
	member_id	integer,
	primary key (trainer_id, member_id),
	foreign key (trainer_id) 	references trainer,
	foreign key (member_id) 	references members
	);

create table group_class_has_session_registration
	(registration_id	integer,
	class_id			integer,
	primary key (registration_id, class_id),
	foreign key (registration_id) 	references session_registration,
	foreign key (class_id) 			references group_class
	);

create table personal_training_session_has_session_registration
	(registration_id	integer,
	pt_id				integer,
	primary key (registration_id, pt_id),
	foreign key (registration_id) 	references session_registration,
	foreign key (pt_id) 			references personal_training_session
	);

create table member_manages_session_registration
	(registration_id	integer,
	member_id			integer,
	primary key (registration_id, member_id),
	foreign key (registration_id) 	references session_registration,
	foreign key (member_id) 		references members
	);
