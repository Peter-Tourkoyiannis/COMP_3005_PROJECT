# fitness_club_functions.py
import psycopg2

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_connection():
    conn = psycopg2.connect(
        dbname="COMP3005 Final",
        user="postgres",
        password="Ary22456",
        host="localhost",
        port="5432"
    )
    return conn

# -----------------------------
# MEMBER FUNCTIONS
# -----------------------------

def register_member(conn, email, first_name, last_name, username, password, dob, gender):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users(email, first_name, last_name)
            VALUES (%s, %s, %s) RETURNING user_id;
        """, (email, first_name, last_name))
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO members(user_id, username, user_password, date_of_birth, gender)
            VALUES (%s, %s, %s, %s, %s);
        """, (user_id, username, password, dob, gender))

        conn.commit()
        return "Member registered successfully"
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return "Error: Email or Username already exists"
    finally:
        cursor.close()

def log_health_metric(conn, member_id, metric_type, unit, recorded_date):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_metrics(member_id, metric_type, unit, recorded_date)
        VALUES (%s, %s, %s, %s);
    """, (member_id, metric_type, unit, recorded_date))
    conn.commit()
    cursor.close()
    return "Health metric logged successfully"

def schedule_pt_session(conn, member_id, trainer_id, start_time, duration):
    cursor = conn.cursor()

    # Check trainer availability
    cursor.execute("""
        SELECT COUNT(*) 
        FROM training_session ts
        JOIN trainer_reviews_training_session tr ON ts.session_id = tr.session_id
        WHERE tr.trainer_id = %s
          AND ts.availability = TRUE
          AND ts.start_time < %s + %s
          AND ts.start_time + ts.duration > %s;
    """, (trainer_id, start_time, duration, start_time))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        return "Trainer not available at this time"

    # Check member availability
    cursor.execute("""
        SELECT COUNT(*)
        FROM member_manages_session_registration mr
        JOIN personal_training_session_has_session_registration ptsr ON mr.registration_id = ptsr.registration_id
        JOIN training_session ts ON ptsr.pt_id = ts.session_id
        WHERE mr.member_id = %s
          AND ts.start_time < %s + %s
          AND ts.start_time + ts.duration > %s;
    """, (member_id, start_time, duration, start_time))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        return "Member already has a session at this time"

    # Insert session
    cursor.execute("""
        INSERT INTO training_session(start_time, duration, availability, session_notes)
        VALUES (%s, %s, TRUE, 'Personal Training Session') RETURNING session_id;
    """, (start_time, duration))
    session_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO personal_training_session(session_id) VALUES (%s);", (session_id,))
    cursor.execute("INSERT INTO session_registration(class_attendance) VALUES ('Scheduled') RETURNING registration_id;")
    reg_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO personal_training_session_has_session_registration(registration_id, pt_id)
        VALUES (%s, %s);
    """, (reg_id, session_id))

    cursor.execute("""
        INSERT INTO member_manages_session_registration(registration_id, member_id)
        VALUES (%s, %s);
    """, (reg_id, member_id))

    cursor.execute("""
        INSERT INTO trainer_reviews_training_session(trainer_id, session_id)
        VALUES (%s, %s);
    """, (trainer_id, session_id))

    conn.commit()
    cursor.close()
    return "Personal training session scheduled successfully"

def register_group_class(conn, member_id, class_id):
    cursor = conn.cursor()

    cursor.execute("SELECT capacity, session_id FROM group_class WHERE class_id = %s;", (class_id,))
    class_info = cursor.fetchone()
    if not class_info:
        cursor.close()
        return "Class does not exist"
    capacity, session_id = class_info

    cursor.execute("""
        SELECT COUNT(*) FROM group_class_has_session_registration
        WHERE class_id = %s;
    """, (class_id,))
    if cursor.fetchone()[0] >= capacity:
        cursor.close()
        return "Class is full"

    # Check member conflicts
    cursor.execute("""
        SELECT ts.start_time, ts.duration
        FROM member_manages_session_registration mr
        JOIN session_registration sr ON mr.registration_id = sr.registration_id
        LEFT JOIN personal_training_session_has_session_registration ptsr ON sr.registration_id = ptsr.registration_id
        LEFT JOIN personal_training_session pts ON ptsr.pt_id = pts.pt_id
        LEFT JOIN training_session ts ON ts.session_id = COALESCE(pts.session_id, %s)
        WHERE mr.member_id = %s
          AND ts.start_time IS NOT NULL
          AND ts.start_time < (SELECT start_time FROM training_session WHERE session_id = %s) +
                              (SELECT duration FROM training_session WHERE session_id = %s)
          AND ts.start_time + ts.duration > (SELECT start_time FROM training_session WHERE session_id = %s);
    """, (session_id, member_id, session_id, session_id, session_id))
    conflict = cursor.fetchone()
    if conflict and conflict[0]:
        cursor.close()
        return "Member has a scheduling conflict"

    cursor.execute("INSERT INTO session_registration(class_attendance) VALUES ('Registered') RETURNING registration_id;")
    reg_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO group_class_has_session_registration(registration_id, class_id)
        VALUES (%s, %s);
    """, (reg_id, class_id))

    cursor.execute("""
        INSERT INTO member_manages_session_registration(registration_id, member_id)
        VALUES (%s, %s);
    """, (reg_id, member_id))

    conn.commit()
    cursor.close()
    return "Successfully registered for group class"

def update_member_profile(conn, member_id, username=None, password=None, dob=None, gender=None,
                          goal_type=None, goal_target=None, start_date=None, end_date=None):
    cursor = conn.cursor()
    updates = []
    params = []
    if username:
        updates.append("username = %s")
        params.append(username)
    if password:
        updates.append("user_password = %s")
        params.append(password)
    if dob:
        updates.append("date_of_birth = %s")
        params.append(dob)
    if gender:
        updates.append("gender = %s")
        params.append(gender)
    if updates:
        query = "UPDATE members SET " + ", ".join(updates) + " WHERE member_id = %s;"
        params.append(member_id)
        cursor.execute(query, tuple(params))
    if all([goal_type, goal_target, start_date, end_date]):
        cursor.execute("""
            INSERT INTO fitness_goals(goal_type, target, start_date, end_date, member_id)
            VALUES (%s, %s, %s, %s, %s);
        """, (goal_type, goal_target, start_date, end_date, member_id))
    conn.commit()
    cursor.close()
    return "Profile and fitness goal updated successfully"

def member_dashboard(conn, member_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT metric_type, unit, recorded_date
        FROM health_metrics
        WHERE member_id = %s
        ORDER BY recorded_date DESC
        LIMIT 5;
    """, (member_id,))
    metrics = cursor.fetchall()

    cursor.execute("""
        SELECT goal_type, target, start_date, end_date
        FROM fitness_goals
        WHERE member_id = %s AND end_date >= EXTRACT(EPOCH FROM NOW())::int;
    """, (member_id,))
    goals = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) FROM member_manages_session_registration
        WHERE member_id = %s;
    """, (member_id,))
    past_classes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT ts.start_time, ts.duration
        FROM member_manages_session_registration mr
        JOIN personal_training_session_has_session_registration ptsr
            ON mr.registration_id = ptsr.registration_id
        JOIN training_session ts ON ptsr.pt_id = ts.session_id
        WHERE mr.member_id = %s AND ts.start_time > EXTRACT(EPOCH FROM NOW())::int
        ORDER BY ts.start_time ASC;
    """, (member_id,))
    upcoming = cursor.fetchall()
    cursor.close()
    return {
        "latest_metrics": metrics,
        "active_goals": goals,
        "past_class_count": past_classes,
        "upcoming_sessions": upcoming
    }

# -----------------------------
# TRAINER FUNCTIONS
# -----------------------------
def set_trainer_availability(conn, trainer_id, hours_per_week, availability_periods, working_periods):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM work_schedule
        WHERE trainer_id = %s AND availability_periods = %s;
    """, (trainer_id, availability_periods))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        return "Availability already exists"

    cursor.execute("""
        INSERT INTO work_schedule(trainer_id, hours_per_week, availability_periods, working_periods)
        VALUES (%s, %s, %s, %s);
    """, (trainer_id, hours_per_week, availability_periods, working_periods))
    conn.commit()
    cursor.close()
    return "Trainer availability set successfully"

def view_trainer_sessions(conn, trainer_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ts.session_id, ts.start_time, ts.duration, s.type_of
        FROM training_session ts
        JOIN trainer_reviews_training_session tr ON ts.session_id = tr.session_id
        JOIN schedule s ON ts.schedule_id = s.schedule_id
        WHERE tr.trainer_id = %s;
    """, (trainer_id,))
    sessions = cursor.fetchall()
    cursor.close()
    return sessions

def trainer_member_lookup(conn, trainer_id, member_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.member_id, fg.goal_type, fg.target, hm.metric_type, hm.unit, hm.recorded_date
        FROM members m
        LEFT JOIN fitness_goals fg ON m.member_id = fg.member_id
        LEFT JOIN health_metrics hm ON m.member_id = hm.member_id
        JOIN trainer_views_members tvm ON tvm.member_id = m.member_id
        WHERE tvm.trainer_id = %s
          AND LOWER(m.username) LIKE LOWER(%s)
        ORDER BY hm.recorded_date DESC
        LIMIT 1;
    """, (trainer_id, f"%{member_name}%"))
    result = cursor.fetchall()
    cursor.close()
    return result

# -----------------------------
# ADMIN FUNCTIONS
# -----------------------------
def book_room(conn, room_number, room_type, schedule_id, session_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM room_booking
        WHERE room_number = %s AND schedule_id = %s;
    """, (room_number, schedule_id))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        return "Room already booked for this schedule"

    cursor.execute("""
        INSERT INTO room_booking(room_number, room_type, schedule_id, session_id)
        VALUES (%s, %s, %s, %s);
    """, (room_number, room_type, schedule_id, session_id))
    conn.commit()
    cursor.close()
    return "Room booked successfully"

def log_equipment_issue(conn, equipment_id, admin_id, status, record):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE equipment
        SET operational_status = FALSE,
            maintenance_status = %s,
            maintenance_records = %s
        WHERE equipment_id = %s;
    """, (status, record, equipment_id))
    cursor.execute("""
        INSERT INTO admin_manages_equipment(equipment_id, admin_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
    """, (equipment_id, admin_id))
    conn.commit()
    cursor.close()
    return "Equipment issue logged successfully"

def create_class(conn, capacity, session_id):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO group_class(capacity, session_id) VALUES (%s, %s);", (capacity, session_id))
    conn.commit()
    cursor.close()
    return "Class created"

def generate_invoice(conn, member_id, amount_due, due_date):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoice(status, amount_due, due_date)
        VALUES ('Pending', %s, %s) RETURNING invoice_id;
    """, (amount_due, due_date))
    invoice_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO member_pays_invoice(invoice_id, member_id)
        VALUES (%s, %s);
    """, (invoice_id, member_id))
    conn.commit()
    cursor.close()
    return f"Invoice {invoice_id} generated for member {member_id}"

# -----------------------------
# DEMO SCRIPT
# -----------------------------
if __name__ == "__main__":
    conn = get_connection()

    print(register_member(conn, "jane@example.com", "Jane", "Doe", "janedoe", "pass123", 631152000, "F"))
    print(log_health_metric(conn, 1, "Weight", "kg", 1704067200))
    print(schedule_pt_session(conn, 1, 1, 1709505600, 60))
    print(register_group_class(conn, 1, 1))
    print(update_member_profile(conn, 1, username="janedoe2", goal_type="Lose Weight", goal_target="60kg", start_date=1704067200, end_date=1709505600))
    print(member_dashboard(conn, 1))
    print(set_trainer_availability(conn, 1, 40, "Mon-Fri 9-12", "Mon-Fri 9-17"))
    print(view_trainer_sessions(conn, 1))
    print(trainer_member_lookup(conn, 1, "janedoe"))
    print(book_room(conn, 101, "Studio", 1, 1))
    print(log_equipment_issue(conn, 1, 1, "Broken", "Treadmill belt needs replacement"))
    print(create_class(conn, 10, 1))
    print(generate_invoice(conn, 1, 100, 1712185600))

    conn.close()
