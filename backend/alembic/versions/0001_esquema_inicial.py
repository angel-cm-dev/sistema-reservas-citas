"""Esquema inicial del sistema de reservas.

Revision ID: 0001
Revises:
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(160), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "services",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("duration_minutes", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
    )

    op.create_table(
        "professionals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), unique=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("specialty", sa.String(120), nullable=False),
        sa.Column("bio", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False),
    )

    op.create_table(
        "professional_services",
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("service_id", sa.Integer, sa.ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "working_hours",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("weekday", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_working_hours_weekday"),
        sa.CheckConstraint("end_time > start_time", name="ck_working_hours_range"),
    )

    op.create_table(
        "schedule_exceptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id", ondelete="CASCADE")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("start_time", sa.Time),
        sa.Column("end_time", sa.Time),
        sa.Column("reason", sa.String(200), nullable=False),
    )
    op.create_index("ix_schedule_exceptions_date", "schedule_exceptions", ["date"])
    op.create_index("ix_schedule_exceptions_professional_id", "schedule_exceptions", ["professional_id"])

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("professional_id", sa.Integer, sa.ForeignKey("professionals.id"), nullable=False),
        sa.Column("service_id", sa.Integer, sa.ForeignKey("services.id"), nullable=False),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("start_at", sa.DateTime, nullable=False),
        sa.Column("end_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("cancellation_reason", sa.String(300)),
        sa.Column("reschedule_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_at > start_at", name="ck_appointments_range"),
    )
    op.create_index("ix_appointments_prof_start", "appointments", ["professional_id", "start_at"])
    op.create_index("ix_appointments_client_id", "appointments", ["client_id"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    op.create_table(
        "reminder_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("appointment_id", sa.Integer, sa.ForeignKey("appointments.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.String(160), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("sent_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("appointment_id", "kind", name="uq_reminder_once"),
    )


def downgrade() -> None:
    for table in ("reminder_logs", "appointments", "schedule_exceptions", "working_hours",
                  "professional_services", "professionals", "services", "users"):
        op.drop_table(table)
