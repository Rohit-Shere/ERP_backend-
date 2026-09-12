import os

import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Fetch variables
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured. Add it to your .env file.")
    return psycopg2.connect(DATABASE_URL)


def run_sql_statements(statements: list[str]) -> None:
    connection = None
    try:
        connection = get_connection()
        connection.autocommit = False
        cursor = connection.cursor()
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
        connection.commit()
    except Exception as error:
        if connection:
            connection.rollback()
        raise RuntimeError(f"Database bootstrap failed: {error}") from error
    finally:
        if connection:
            connection.close()


# ============================================================
# SQL SCHEMA
# ============================================================

CREATE_TABLES_SQL = """

-- =========================================================
-- 1. DEPARTMENT
-- =========================================================

CREATE TABLE IF NOT EXISTS department (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    department_code VARCHAR(20) NOT NULL UNIQUE,

    department_name VARCHAR(150) NOT NULL UNIQUE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 2. EMPLOYEE CATEGORY
-- =========================================================

CREATE TABLE IF NOT EXISTS employee_category (
    category_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    category_code VARCHAR(20) NOT NULL UNIQUE,

    category_name VARCHAR(100) NOT NULL UNIQUE,

    description TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 3. EMPLOYEE
-- =========================================================

CREATE TABLE IF NOT EXISTS employee (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_code VARCHAR(30) NOT NULL UNIQUE,

    first_name VARCHAR(100) NOT NULL,

    last_name VARCHAR(100),

    email VARCHAR(255) NOT NULL UNIQUE,

    phone VARCHAR(20),

    designation VARCHAR(150),

    department_id BIGINT NOT NULL,

    category_id SMALLINT NOT NULL,

    joining_date DATE,

    employment_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_employee_department
        FOREIGN KEY (department_id)
        REFERENCES department(department_id),

    CONSTRAINT fk_employee_category
        FOREIGN KEY (category_id)
        REFERENCES employee_category(category_id),

    CONSTRAINT chk_employee_status
        CHECK (
            employment_status IN (
                'ACTIVE',
                'INACTIVE',
                'RESIGNED',
                'RETIRED',
                'TERMINATED'
            )
        )
);


-- =========================================================
-- 4. USER ACCOUNT AND ROLE
-- =========================================================

CREATE TABLE IF NOT EXISTS user_account (
    user_id UUID PRIMARY KEY,

    employee_id BIGINT NOT NULL UNIQUE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_account_employee
        FOREIGN KEY (employee_id)
        REFERENCES employee(employee_id)
);


CREATE TABLE IF NOT EXISTS user_role (
    user_id UUID NOT NULL,

    role VARCHAR(30) NOT NULL,

    department_id BIGINT,

    PRIMARY KEY (user_id, role),

    CONSTRAINT fk_user_role_account
        FOREIGN KEY (user_id)
        REFERENCES user_account(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_role_department
        FOREIGN KEY (department_id)
        REFERENCES department(department_id),

    CONSTRAINT chk_user_role
        CHECK (role IN ('EMPLOYEE', 'DEPARTMENT_HEAD', 'ADMIN'))
);


CREATE INDEX IF NOT EXISTS idx_user_role_department
    ON user_role(department_id);


-- =========================================================
-- 5. LEAVE TYPE
-- =========================================================

CREATE TABLE IF NOT EXISTS leave_type (
    leave_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    leave_code VARCHAR(20) NOT NULL UNIQUE,

    leave_name VARCHAR(100) NOT NULL UNIQUE,

    description TEXT,

    unit VARCHAR(20) NOT NULL DEFAULT 'DAYS',

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_leave_unit
        CHECK (unit IN ('DAYS', 'HOURS'))
);


-- =========================================================
-- 5. LEAVE ENTITLEMENT
-- =========================================================

CREATE TABLE IF NOT EXISTS leave_entitlement (
    entitlement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    category_id SMALLINT NOT NULL,

    leave_type_id BIGINT NOT NULL,

    academic_year VARCHAR(20) NOT NULL,

    entitled_days NUMERIC(6,2) NOT NULL DEFAULT 0,

    max_days NUMERIC(6,2),

    carry_forward_days NUMERIC(6,2) NOT NULL DEFAULT 0,

    warning_threshold NUMERIC(6,2),

    effective_from DATE NOT NULL,

    effective_to DATE NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_entitlement_category
        FOREIGN KEY (category_id)
        REFERENCES employee_category(category_id),

    CONSTRAINT fk_entitlement_leave_type
        FOREIGN KEY (leave_type_id)
        REFERENCES leave_type(leave_type_id),

    CONSTRAINT uq_entitlement
        UNIQUE (
            category_id,
            leave_type_id,
            academic_year
        ),

    CONSTRAINT chk_entitled_days
        CHECK (entitled_days >= 0),

    CONSTRAINT chk_max_days
        CHECK (
            max_days IS NULL
            OR max_days >= entitled_days
        ),

    CONSTRAINT chk_carry_forward
        CHECK (carry_forward_days >= 0),

    CONSTRAINT chk_warning_threshold
        CHECK (
            warning_threshold IS NULL
            OR warning_threshold >= 0
        ),

    CONSTRAINT chk_entitlement_dates
        CHECK (effective_to >= effective_from)
);


-- =========================================================
-- 6. ACADEMIC CALENDAR
-- =========================================================

CREATE TABLE IF NOT EXISTS academic_calendar (
    calendar_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    academic_year VARCHAR(20) NOT NULL UNIQUE,

    calendar_name VARCHAR(150) NOT NULL,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_calendar_dates
        CHECK (end_date >= start_date)
);


-- =========================================================
-- 7. CALENDAR EVENT
-- =========================================================

CREATE TABLE IF NOT EXISTS calendar_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    calendar_id BIGINT NOT NULL,

    event_date DATE NOT NULL,

    event_type VARCHAR(50) NOT NULL,

    description TEXT,

    is_working_day BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_calendar_event_calendar
        FOREIGN KEY (calendar_id)
        REFERENCES academic_calendar(calendar_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_calendar_event
        UNIQUE (
            calendar_id,
            event_date
        )
);


-- =========================================================
-- 8. LEAVE APPLICATION
-- =========================================================

CREATE TABLE IF NOT EXISTS leave_application (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_id BIGINT NOT NULL,

    leave_type_id BIGINT NOT NULL,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    requested_days NUMERIC(6,2) NOT NULL,

    calculated_days NUMERIC(6,2) NOT NULL,

    reason TEXT,

    station_leaving BOOLEAN NOT NULL DEFAULT FALSE,

    station_name VARCHAR(200),

    station_contact_number VARCHAR(20),

    status VARCHAR(40) NOT NULL DEFAULT 'PENDING_DEPARTMENT_HEAD',

    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_application_employee
        FOREIGN KEY (employee_id)
        REFERENCES employee(employee_id),

    CONSTRAINT fk_application_leave_type
        FOREIGN KEY (leave_type_id)
        REFERENCES leave_type(leave_type_id),

    CONSTRAINT chk_application_dates
        CHECK (end_date >= start_date),

    CONSTRAINT chk_requested_days
        CHECK (requested_days > 0),

    CONSTRAINT chk_calculated_days
        CHECK (calculated_days > 0),

    CONSTRAINT chk_application_status
        CHECK (
            status IN (
                'PENDING_DEPARTMENT_HEAD',
                'DEPARTMENT_APPROVED',
                'DEPARTMENT_REJECTED',
                'PENDING_ADMIN',
                'ADMIN_APPROVED',
                'ADMIN_REJECTED',
                'CANCELLED'
            )
        ),

    CONSTRAINT chk_station_details
        CHECK (
            station_leaving = TRUE
            OR (
                station_name IS NULL
                AND station_contact_number IS NULL
            )
        )
);


-- =========================================================
-- 9. APPROVAL HISTORY
-- =========================================================

CREATE TABLE IF NOT EXISTS approval_history (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL,

    approver_id BIGINT NOT NULL,

    approver_role VARCHAR(30) NOT NULL,

    action VARCHAR(20) NOT NULL,

    comments TEXT,

    action_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_approval_application
        FOREIGN KEY (application_id)
        REFERENCES leave_application(application_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_approval_employee
        FOREIGN KEY (approver_id)
        REFERENCES employee(employee_id),

    CONSTRAINT chk_approver_role
        CHECK (
            approver_role IN (
                'DEPARTMENT_HEAD',
                'ADMIN'
            )
        ),

    CONSTRAINT chk_approval_action
        CHECK (
            action IN (
                'APPROVED',
                'REJECTED'
            )
        )
);


-- =========================================================
-- 10. LEAVE RECORD
-- =========================================================

CREATE TABLE IF NOT EXISTS leave_record (
    leave_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL UNIQUE,

    employee_id BIGINT NOT NULL,

    leave_type_id BIGINT NOT NULL,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    calculated_days NUMERIC(6,2) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'TAKEN',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_leave_record_application
        FOREIGN KEY (application_id)
        REFERENCES leave_application(application_id),

    CONSTRAINT fk_leave_record_employee
        FOREIGN KEY (employee_id)
        REFERENCES employee(employee_id),

    CONSTRAINT fk_leave_record_type
        FOREIGN KEY (leave_type_id)
        REFERENCES leave_type(leave_type_id),

    CONSTRAINT chk_leave_record_dates
        CHECK (end_date >= start_date),

    CONSTRAINT chk_leave_record_days
        CHECK (calculated_days > 0),

    CONSTRAINT chk_leave_record_status
        CHECK (
            status IN (
                'TAKEN',
                'CANCELLED',
                'REVOKED'
            )
        )
);


-- =========================================================
-- 11. LEAVE ATTACHMENT
-- =========================================================

CREATE TABLE IF NOT EXISTS leave_attachment (
    attachment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    application_id BIGINT NOT NULL,

    document_type VARCHAR(50) NOT NULL,

    file_name VARCHAR(255) NOT NULL,

    file_path TEXT NOT NULL,

    file_hash VARCHAR(128),

    verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_attachment_application
        FOREIGN KEY (application_id)
        REFERENCES leave_application(application_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_attachment_status
        CHECK (
            verification_status IN (
                'PENDING',
                'VERIFIED',
                'REJECTED'
            )
        )
);


-- =========================================================
-- 12. LEAVE ALERT
-- =========================================================

CREATE TABLE IF NOT EXISTS leave_alert (
    alert_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_id BIGINT NOT NULL,

    leave_type_id BIGINT NOT NULL,

    leave_id BIGINT,

    academic_year VARCHAR(20) NOT NULL,

    alert_type VARCHAR(40) NOT NULL,

    severity VARCHAR(20) NOT NULL,

    threshold_value NUMERIC(6,2),

    actual_value NUMERIC(6,2) NOT NULL,

    message TEXT NOT NULL,

    is_read BOOLEAN NOT NULL DEFAULT FALSE,

    email_sent BOOLEAN NOT NULL DEFAULT FALSE,

    email_sent_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    resolved_at TIMESTAMPTZ,

    CONSTRAINT fk_alert_employee
        FOREIGN KEY (employee_id)
        REFERENCES employee(employee_id),

    CONSTRAINT fk_alert_leave_type
        FOREIGN KEY (leave_type_id)
        REFERENCES leave_type(leave_type_id),

    CONSTRAINT fk_alert_leave
        FOREIGN KEY (leave_id)
        REFERENCES leave_record(leave_id),

    CONSTRAINT chk_alert_type
        CHECK (
            alert_type IN (
                'APPROACHING_LIMIT',
                'LIMIT_REACHED',
                'LIMIT_EXCEEDED'
            )
        ),

    CONSTRAINT chk_alert_severity
        CHECK (
            severity IN (
                'INFO',
                'WARNING',
                'CRITICAL'
            )
        )
);


-- =========================================================
-- 13. INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_employee_department
    ON employee(department_id);

CREATE INDEX IF NOT EXISTS idx_employee_category
    ON employee(category_id);

CREATE INDEX IF NOT EXISTS idx_employee_status
    ON employee(employment_status);


CREATE INDEX IF NOT EXISTS idx_leave_application_employee
    ON leave_application(employee_id);

CREATE INDEX IF NOT EXISTS idx_leave_application_status
    ON leave_application(status);

CREATE INDEX IF NOT EXISTS idx_leave_application_dates
    ON leave_application(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_leave_application_type
    ON leave_application(leave_type_id);


CREATE INDEX IF NOT EXISTS idx_approval_application
    ON approval_history(application_id);

CREATE INDEX IF NOT EXISTS idx_approval_approver
    ON approval_history(approver_id);


CREATE INDEX IF NOT EXISTS idx_leave_record_employee
    ON leave_record(employee_id);

CREATE INDEX IF NOT EXISTS idx_leave_record_type
    ON leave_record(leave_type_id);

CREATE INDEX IF NOT EXISTS idx_leave_record_dates
    ON leave_record(start_date, end_date);


CREATE INDEX IF NOT EXISTS idx_alert_employee
    ON leave_alert(employee_id);

CREATE INDEX IF NOT EXISTS idx_alert_unread
    ON leave_alert(employee_id, is_read);

CREATE INDEX IF NOT EXISTS idx_alert_email
    ON leave_alert(email_sent);


CREATE INDEX IF NOT EXISTS idx_calendar_event_date
    ON calendar_event(calendar_id, event_date);


-- =========================================================
-- PREVENT DUPLICATE ALERTS
-- =========================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_leave_alert_threshold
ON leave_alert (
    employee_id,
    leave_type_id,
    academic_year,
    alert_type
);

"""


# ============================================================
# SEED MASTER DATA
# ============================================================

SEED_DATA_SQL = """

-- =========================================================
-- EMPLOYEE CATEGORIES
-- =========================================================

INSERT INTO employee_category
    (category_code, category_name, description)
VALUES
    (
        'TV',
        'Teaching - Vacational',
        'Teaching staff following vacation-based academic schedule'
    ),
    (
        'TNV',
        'Teaching - Non-Vacational',
        'Teaching staff following non-vacational leave structure'
    ),
    (
        'NT',
        'Non-Teaching / Administrative',
        'Administrative and non-teaching employees'
    ),
    (
        'VC',
        'Vocational / Contractual',
        'Vocational and contractual employees'
    )
ON CONFLICT (category_code)
DO NOTHING;


-- =========================================================
-- LEAVE TYPES
-- =========================================================

INSERT INTO leave_type
    (leave_code, leave_name, description, unit)
VALUES
    (
        'CL',
        'Casual Leave',
        'Casual leave',
        'DAYS'
    ),
    (
        'EL',
        'Earned Leave',
        'Earned leave',
        'DAYS'
    ),
    (
        'ML',
        'Medical Leave',
        'Medical leave',
        'DAYS'
    ),
    (
        'DL',
        'Duty Leave',
        'Leave for official duty',
        'DAYS'
    ),
    (
        'VL',
        'Vacation Leave',
        'Academic vacation leave',
        'DAYS'
    ),
    (
        'LOP',
        'Loss of Pay',
        'Leave without pay',
        'DAYS'
    )
ON CONFLICT (leave_code)
DO NOTHING;

"""





# ============================================================
# CREATE DATABASE SCHEMA
# ============================================================

def create_database_schema():
    try:
        print("Connecting to PostgreSQL...")
        print("Creating database tables...")
        print("Inserting master data...")
        run_sql_statements([CREATE_TABLES_SQL, SEED_DATA_SQL])

        print("\n======================================")
        print("DATABASE CREATED SUCCESSFULLY")
        print("======================================")

    except Exception as error:
        print("\nERROR:")
        print(error)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    create_database_schema()