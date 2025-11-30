# COMP3005 Final Project – Health & Fitness Club Management System
# Functions rewritten to match the given PostgreSQL schema exactly.

import psycopg2


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_connection():
    """
    Update the connection parameters to match your local PostgreSQL setup.
    """
    conn = psycopg2.connect(
        dbname="COMP3005 Final",
        user="postgres",
        password="Ary22456",  # <- CHANGE THIS
        host="localhost",
        port="5432",
    )
    return conn


# ============================================================
# ===============        MEMBER FUNCTIONS       ==============
# ============================================================

def register_member(conn, email, first_name, last_name, username, password, dob, gender):
    """
    Member Registration:
    1. Insert into users (unique email).
    2. Insert into members (unique username, linked by user_id).
    """
    cur = conn.cursor()
    try:
        # Insert user
        cur.execute(
            """
            INSERT INTO users (email, first_name, last_name)
            VALUES (%s, %s, %s)
            RETURNING user_id;
            """,
            (email, first_name, last_name),
        )
        user_id = cur.fetchone()[0]

        # Insert member profile
        cur.execute(
            """
            INSERT INTO members (user_id, username, user_password, date_of_birth, gender)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING member_id;
            """,
            (user_id, username, password, dob, gender),
        )
        member_id = cur.fetchone()[0]

        conn.commit()
        return f"Member registered successfully with member_id = {member_id}"

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return "Error: Email or username already exists"
    except Exception as e:
        conn.rollback()
        return f"Error registering member: {e}"
    finally:
        cur.close()


def log_health_metric(conn, member_id, metric_type, unit, recorded_date):
    """
    Health History:
    Add a new health_metrics row (does not overwrite old metrics).
    """
    cur = conn.cursor()
    try:
        # Ensure member exists
        cur.execute("SELECT 1 FROM members WHERE member_id = %s;", (member_id,))
        if not cur.fetchone():
            return f"Error: Member {member_id} does not exist"

        cur.execute(
            """
            INSERT INTO health_metrics (metric_type, unit, recorded_date, member_id)
            VALUES (%s, %s, %s, %s);
            """,
            (metric_type, unit, recorded_date, member_id),
        )
        conn.commit()
        return "Health metric logged successfully"
    except Exception as e:
        conn.rollback()
        return f"Error logging health metric: {e}"
    finally:
        cur.close()


def update_member_profile(
    conn,
    member_id,
    username=None,
    password=None,
    dob=None,
    gender=None,
    goal_type=None,
    goal_target=None,
    start_date=None,
    end_date=None,
):
    """
    Profile Management:
    - Optionally update member's username, password, DOB, gender.
    - Optionally insert a new fitness goal (if goal fields are provided).
    """
    cur = conn.cursor()
    try:
        # Ensure member exists
        cur.execute("SELECT 1 FROM members WHERE member_id = %s;", (member_id,))
        if not cur.fetchone():
            return f"Error: Member {member_id} does not exist"

        # Build dynamic UPDATE for members
        updates = []
        params = []

        if username is not None:
            updates.append("username = %s")
            params.append(username)
        if password is not None:
            updates.append("user_password = %s")
            params.append(password)
        if dob is not None:
            updates.append("date_of_birth = %s")
            params.append(dob)
        if gender is not None:
            updates.append("gender = %s")
            params.append(gender)

        if updates:
            query = "UPDATE members SET " + ", ".join(updates) + " WHERE member_id = %s;"
            params.append(member_id)
            cur.execute(query, tuple(params))

        # Insert fitness goal if all fields provided
        if all(v is not None for v in [goal_type, goal_target, start_date, end_date]):
            cur.execute(
                """
                INSERT INTO fitness_goals (goal_type, target, start_date, end_date, member_id)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (goal_type, goal_target, start_date, end_date, member_id),
            )

        conn.commit()
        return "Profile (and goal, if provided) updated successfully"

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return "Error: Username already exists"
    except Exception as e:
        conn.rollback()
        return f"Error updating profile: {e}"
    finally:
        cur.close()


def schedule_pt_session(conn, member_id, trainer_id, start_time, duration):
    """
    PT Session Scheduling:
    - Ensure member and trainer exist.
    - Prevent overlapping sessions for trainer and member.
    - Create a training_session + personal_training_session + necessary link rows.
    """
    cur = conn.cursor()
    try:
        # --- Validate member & trainer ---
        cur.execute("SELECT 1 FROM members WHERE member_id = %s;", (member_id,))
        if not cur.fetchone():
            return f"Error: Member {member_id} does not exist"

        cur.execute("SELECT 1 FROM trainer WHERE trainer_id = %s;", (trainer_id,))
        if not cur.fetchone():
            return f"Error: Trainer {trainer_id} does not exist"

        # --- Check trainer availability (no overlapping sessions) ---
        cur.execute(
            """
            SELECT COUNT(*)
            FROM training_session ts
            JOIN trainer_reviews_training_session tr
              ON ts.session_id = tr.session_id
            WHERE tr.trainer_id = %s
              AND ts.start_time < %s + %s
              AND ts.start_time + ts.duration > %s;
            """,
            (trainer_id, start_time, duration, start_time),
        )
        if cur.fetchone()[0] > 0:
            return "Trainer not available at this time"

        # --- Check member availability (PT + group classes) ---
        cur.execute(
            """
            SELECT COUNT(*)
            FROM member_manages_session_registration mm
            JOIN session_registration sr
              ON mm.registration_id = sr.registration_id
            LEFT JOIN personal_training_session_has_session_registration ptsr
              ON sr.registration_id = ptsr.registration_id
            LEFT JOIN personal_training_session pts
              ON ptsr.pt_id = pts.pt_id
            LEFT JOIN group_class_has_session_registration gcsr
              ON sr.registration_id = gcsr.registration_id
            LEFT JOIN group_class gc
              ON gcsr.class_id = gc.class_id
            LEFT JOIN training_session ts
              ON ts.session_id = COALESCE(pts.session_id, gc.session_id)
            WHERE mm.member_id = %s
              AND ts.start_time IS NOT NULL
              AND ts.start_time < %s + %s
              AND ts.start_time + ts.duration > %s;
            """,
            (member_id, start_time, duration, start_time),
        )
        if cur.fetchone()[0] > 0:
            return "Member already has a session at this time"

        # --- Create training_session ---
        cur.execute(
            """
            INSERT INTO training_session (availability, session_notes, start_time, duration, schedule_id)
            VALUES (TRUE, %s, %s, %s, NULL)
            RETURNING session_id;
            """,
            (f"Personal Training Session for member {member_id}", start_time, duration),
        )
        session_id = cur.fetchone()[0]

        # --- Create personal_training_session row ---
        cur.execute(
            """
            INSERT INTO personal_training_session (session_id)
            VALUES (%s)
            RETURNING pt_id;
            """,
            (session_id,),
        )
        pt_id = cur.fetchone()[0]

        # --- Create session_registration row ---
        cur.execute(
            """
            INSERT INTO session_registration (class_attendance)
            VALUES ('Scheduled PT Session')
            RETURNING registration_id;
            """
        )
        registration_id = cur.fetchone()[0]

        # --- Link tables ---
        cur.execute(
            """
            INSERT INTO personal_training_session_has_session_registration (registration_id, pt_id)
            VALUES (%s, %s);
            """,
            (registration_id, pt_id),
        )

        cur.execute(
            """
            INSERT INTO member_manages_session_registration (registration_id, member_id)
            VALUES (%s, %s);
            """,
            (registration_id, member_id),
        )

        cur.execute(
            """
            INSERT INTO trainer_reviews_training_session (session_id, trainer_id)
            VALUES (%s, %s);
            """,
            (session_id, trainer_id),
        )

        conn.commit()
        return f"PT session {session_id} scheduled for member {member_id} with trainer {trainer_id}"

    except Exception as e:
        conn.rollback()
        return f"Error scheduling PT session: {e}"
    finally:
        cur.close()


def register_group_class(conn, member_id, class_id):
    """
    Group Class Registration:
    - Check class exists and capacity not exceeded.
    - Check the member has no time conflict with this class.
    - Insert into session_registration, group_class_has_session_registration, member_manages_session_registration.
    """
    cur = conn.cursor()
    try:
        # Ensure member exists
        cur.execute("SELECT 1 FROM members WHERE member_id = %s;", (member_id,))
        if not cur.fetchone():
            return f"Error: Member {member_id} does not exist"

        # Get class info
        cur.execute(
            """
            SELECT capacity, session_id
            FROM group_class
            WHERE class_id = %s;
            """,
            (class_id,),
        )
        row = cur.fetchone()
        if not row:
            return "Error: Class does not exist"
        capacity, session_session_id = row

        # Check capacity
        cur.execute(
            """
            SELECT COUNT(*)
            FROM group_class_has_session_registration
            WHERE class_id = %s;
            """,
            (class_id,),
        )
        current_count = cur.fetchone()[0]
        if current_count >= capacity:
            return "Error: Class is full"

        # Get the class session time
        cur.execute(
            """
            SELECT ts.start_time, ts.duration
            FROM training_session ts
            WHERE ts.session_id = %s;
            """,
            (session_session_id,),
        )
        class_time = cur.fetchone()
        if not class_time:
            return "Error: Training session for this class does not exist"
        class_start, class_duration = class_time

        # Check member time conflicts (PT + other group classes)
        cur.execute(
            """
            SELECT COUNT(*)
            FROM member_manages_session_registration mm
            JOIN session_registration sr
              ON mm.registration_id = sr.registration_id
            LEFT JOIN personal_training_session_has_session_registration ptsr
              ON sr.registration_id = ptsr.registration_id
            LEFT JOIN personal_training_session pts
              ON ptsr.pt_id = pts.pt_id
            LEFT JOIN group_class_has_session_registration gcsr
              ON sr.registration_id = gcsr.registration_id
            LEFT JOIN group_class gc
              ON gcsr.class_id = gc.class_id
            LEFT JOIN training_session ts
              ON ts.session_id = COALESCE(pts.session_id, gc.session_id)
            WHERE mm.member_id = %s
              AND ts.start_time IS NOT NULL
              AND ts.start_time < %s + %s
              AND ts.start_time + ts.duration > %s;
            """,
            (member_id, class_start, class_duration, class_start),
        )
        if cur.fetchone()[0] > 0:
            return "Error: Member has a scheduling conflict with this class"

        # Create new registration
        cur.execute(
            """
            INSERT INTO session_registration (class_attendance)
            VALUES ('Registered for group class')
            RETURNING registration_id;
            """
        )
        registration_id = cur.fetchone()[0]

        # Link to group_class
        cur.execute(
            """
            INSERT INTO group_class_has_session_registration (registration_id, class_id)
            VALUES (%s, %s);
            """,
            (registration_id, class_id),
        )

        # Link to member
        cur.execute(
            """
            INSERT INTO member_manages_session_registration (registration_id, member_id)
            VALUES (%s, %s);
            """,
            (registration_id, member_id),
        )

        conn.commit()
        return f"Member {member_id} successfully registered for class {class_id}"

    except Exception as e:
        conn.rollback()
        return f"Error registering for group class: {e}"
    finally:
        cur.close()


# ============================================================
# ===============       TRAINER FUNCTIONS      ===============
# ============================================================

def set_trainer_availability(conn, trainer_id, hours_per_week, availability_periods, working_periods):
    """
    Trainer Set Availability:
    - Make sure trainer exists.
    - Prevent duplicate availability_periods for same trainer.
    - Insert a row into work_schedule.
    """
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM trainer WHERE trainer_id = %s;", (trainer_id,))
        if not cur.fetchone():
            return f"Error: Trainer {trainer_id} does not exist"

        # Avoid duplicate availability entries
        cur.execute(
            """
            SELECT COUNT(*)
            FROM work_schedule
            WHERE trainer_id = %s AND availability_periods = %s;
            """,
            (trainer_id, availability_periods),
        )
        if cur.fetchone()[0] > 0:
            return "Error: This availability already exists for this trainer"

        cur.execute(
            """
            INSERT INTO work_schedule (hours_per_week, availability_periods, working_periods, trainer_id)
            VALUES (%s, %s, %s, %s)
            RETURNING trainer_schedule_id;
            """,
            (hours_per_week, availability_periods, working_periods, trainer_id),
        )
        sched_id = cur.fetchone()[0]
        conn.commit()
        return f"Trainer availability set (schedule_id = {sched_id})"
    except Exception as e:
        conn.rollback()
        return f"Error setting trainer availability: {e}"
    finally:
        cur.close()


def view_trainer_sessions(conn, trainer_id):
    """
    Trainer Schedule View:
    - List sessions assigned to the trainer (PT + group).
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT ts.session_id,
                   ts.start_time,
                   ts.duration,
                   s.type_of
            FROM training_session ts
            JOIN trainer_reviews_training_session tr
              ON ts.session_id = tr.session_id
            LEFT JOIN schedule s
              ON ts.schedule_id = s.schedule_id
            WHERE tr.trainer_id = %s
            ORDER BY ts.start_time;
            """,
            (trainer_id,),
        )
        rows = cur.fetchall()
        return rows
    except Exception as e:
        return f"Error viewing trainer sessions: {e}"
    finally:
        cur.close()


def trainer_member_lookup(conn, trainer_id, member_name):
    """
    Trainer Member Lookup:
    - Search by username (case-insensitive).
    - Only for members the trainer is allowed to view (trainer_views_members).
    - Return latest health metric + goal information.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT m.member_id,
                   m.username,
                   fg.goal_type,
                   fg.target,
                   hm.metric_type,
                   hm.unit,
                   hm.recorded_date
            FROM trainer_views_members tvm
            JOIN members m
              ON tvm.member_id = m.member_id
            LEFT JOIN fitness_goals fg
              ON fg.member_id = m.member_id
            LEFT JOIN health_metrics hm
              ON hm.member_id = m.member_id
            WHERE tvm.trainer_id = %s
              AND LOWER(m.username) LIKE LOWER(%s)
            ORDER BY hm.recorded_date DESC NULLS LAST
            LIMIT 1;
            """,
            (trainer_id, f"%{member_name}%"),
        )
        row = cur.fetchone()
        if not row:
            return "No matching member found or trainer has no access"
        return row
    except Exception as e:
        return f"Error during trainer member lookup: {e}"
    finally:
        cur.close()


# ============================================================
# ===============       ADMIN FUNCTIONS        ===============
# ============================================================

def book_room(conn, room_number, room_type, schedule_id, session_id):
    """
    Room Booking (Admin):
    - Prevent double-booking same room for same schedule_id.
    - Insert row into room_booking.
    """
    cur = conn.cursor()
    try:
        # Check for double booking (same room, same schedule)
        cur.execute(
            """
            SELECT COUNT(*)
            FROM room_booking
            WHERE room_number = %s AND schedule_id = %s;
            """,
            (room_number, schedule_id),
        )
        if cur.fetchone()[0] > 0:
            return "Error: Room already booked for this schedule"

        cur.execute(
            """
            INSERT INTO room_booking (room_number, room_type, schedule_id, session_id)
            VALUES (%s, %s, %s, %s)
            RETURNING room_id;
            """,
            (room_number, room_type, schedule_id, session_id),
        )
        room_id = cur.fetchone()[0]
        conn.commit()
        return f"Room booked successfully (room_id = {room_id})"
    except Exception as e:
        conn.rollback()
        return f"Error booking room: {e}"
    finally:
        cur.close()


def log_equipment_issue(conn, equipment_id, admin_id, status, record):
    """
    Equipment Maintenance (Admin):
    - Update equipment status & maintenance fields.
    - Make sure admin_manages_equipment has (equipment_id, admin_id).
    """
    cur = conn.cursor()
    try:
        # Ensure equipment exists
        cur.execute("SELECT 1 FROM equipment WHERE equipment_id = %s;", (equipment_id,))
        if not cur.fetchone():
            return f"Error: Equipment {equipment_id} does not exist"

        # Update equipment record
        cur.execute(
            """
            UPDATE equipment
            SET operational_status = FALSE,
                maintenance_status = %s,
                maintenance_records = %s
            WHERE equipment_id = %s;
            """,
            (status, record, equipment_id),
        )

        # Link admin -> equipment (avoid duplicates)
        cur.execute(
            """
            INSERT INTO admin_manages_equipment (equipment_id, admin_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (equipment_id, admin_id),
        )

        conn.commit()
        return "Equipment issue logged successfully"
    except Exception as e:
        conn.rollback()
        return f"Error logging equipment issue: {e}"
    finally:
        cur.close()


def create_class(conn, capacity, session_id):
    """
    Class Management (Admin):
    - Create a new group_class linked to an existing training_session.
    """
    cur = conn.cursor()
    try:
        # Ensure session exists
        cur.execute("SELECT 1 FROM training_session WHERE session_id = %s;", (session_id,))
        if not cur.fetchone():
            return f"Error: Training session {session_id} does not exist"

        cur.execute(
            """
            INSERT INTO group_class (capacity, session_id)
            VALUES (%s, %s)
            RETURNING class_id;
            """,
            (capacity, session_id),
        )
        class_id = cur.fetchone()[0]
        conn.commit()
        return f"Class created with class_id = {class_id}"
    except Exception as e:
        conn.rollback()
        return f"Error creating class: {e}"
    finally:
        cur.close()


def generate_invoice(conn, member_id, amount_due, due_date):
    """
    Billing & Payment (Admin):
    - Create invoice with status 'Pending'.
    - Link to member via member_pays_invoice.
    """
    cur = conn.cursor()
    try:
        # Ensure member exists
        cur.execute("SELECT 1 FROM members WHERE member_id = %s;", (member_id,))
        if not cur.fetchone():
            return f"Error: Member {member_id} does not exist"

        cur.execute(
            """
            INSERT INTO invoice (status, amount_due, due_date)
            VALUES ('Pending', %s, %s)
            RETURNING invoice_id;
            """,
            (amount_due, due_date),
        )
        invoice_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO member_pays_invoice (invoice_id, member_id)
            VALUES (%s, %s);
            """,
            (invoice_id, member_id),
        )

        conn.commit()
        return f"Invoice {invoice_id} generated for member {member_id}"
    except Exception as e:
        conn.rollback()
        return f"Error generating invoice: {e}"
    finally:
        cur.close()


# ============================================================
# ===============          DEMO MAIN            ===============
# ============================================================

if __name__ == "__main__":
    """
    Simple demo calls – run this file directly AFTER:
    1. Creating the database with your DDL.sql
    2. Loading sample data from DML.sql
    """
    conn = get_connection()

    print("=== MEMBER FUNCTIONS ===")
    print(register_member(conn, "jane@example.com", "Jane", "Doe", "janedoe", "pass123", 20000101, "F"))
    print(log_health_metric(conn, 1, "Weight", "kg", 20251129))
    print(update_member_profile(conn, 1, username="arypat_updated",
                                goal_type="Lose Weight", goal_target="70kg",
                                start_date=20251101, end_date=20260301))
    print(schedule_pt_session(conn, 1, 1, 900, 60))          # 9:00 start, 60 minutes
    print(register_group_class(conn, 1, 1))                  # existing class_id from DML

    print("\n=== TRAINER FUNCTIONS ===")
    print(set_trainer_availability(conn, 1, 40, "Mon-Fri 9-12", "Mon-Fri 9-17"))
    print("Trainer sessions:", view_trainer_sessions(conn, 1))
    print("Trainer member lookup:", trainer_member_lookup(conn, 1, "ary"))

    print("\n=== ADMIN FUNCTIONS ===")
    print(book_room(conn, 102, "Studio", 1, 1))              # new room_number
    print(log_equipment_issue(conn, 1, 1, "Broken", "Belt needs replacement"))
    print(create_class(conn, 15, 1))
    print(generate_invoice(conn, 1, 100, 20251215))

    conn.close()
