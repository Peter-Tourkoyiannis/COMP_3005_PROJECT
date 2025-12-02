-- Not needed (unless ER changes)
create table is_a_trainer
	(user_id	integer,
	trainer_id	integer,
	primary key (user_id, trainer_id),
	foreign key (user_id) 		references users,
	foreign key (trainer_id) 	references trainer
	);

create table is_a_member
	(user_id	integer,
	member_id	integer,
	primary key (user_id, member_id),
	foreign key (user_id) 	references users,
	foreign key (member_id) references members
	);

create table is_a_admin
	(user_id	integer,
	admin_id	integer,
	primary key (user_id, admin_id),
	foreign key (user_id) 	references users,
	foreign key (admin_id) 	references admin_staff
	);
