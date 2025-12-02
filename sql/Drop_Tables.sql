-- Drop 1:N Tables
DROP TABLE personal_training_session_has_session_registration;
DROP TABLE group_class_has_session_registration;
DROP TABLE member_manages_session_registration;
DROP TABLE trainer_views_members;
DROP TABLE trainer_reviews_training_session;
DROP TABLE admin_system_generates_invoice;
DROP TABLE member_pays_invoice;
DROP TABLE admin_system_accesses_members;
DROP TABLE room_booking_has_equipment;
DROP TABLE admin_manages_equipment;
DROP TABLE admin_access_work_schedule;
DROP TABLE admin_manage_schedule;

-- Drop 1:1 / Weak Tables
DROP TABLE personal_training_session;
DROP TABLE group_class;
DROP TABLE session_registration;
DROP TABLE health_metrics;
DROP TABLE fitness_goals;
DROP TABLE work_schedule;
DROP TABLE room_booking;
DROP TABLE training_session;
DROP TABLE schedule;
DROP TABLE invoice;
DROP TABLE equipment;
DROP TABLE admin_system;
DROP TABLE admin_staff;
DROP TABLE members;
DROP TABLE trainer;
DROP TABLE users;
