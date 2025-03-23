"""Initial revision

Revision ID: 85ad94556f79
Revises: 
Create Date: 2025-03-23 14:00:29.426067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85ad94556f79'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hospitals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('hospital_type', sa.Enum('GENERAL', 'SPECIALIZED', 'UNIVERSITY', 'PRIVATE', 'CLINIC', name='hospitaltype'), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('region', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=False),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('website', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('is_user', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('is_super_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('is_donor', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('is_hospital_staff', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone_number')
    )
    op.create_table('donors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('gender', sa.Enum('MALE', 'FEMALE', 'OTHER', name='gender'), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=False),
    sa.Column('blood_type', sa.Enum('O_POSITIVE', 'O_NEGATIVE', 'A_POSITIVE', 'A_NEGATIVE', 'B_POSITIVE', 'B_NEGATIVE', 'AB_POSITIVE', 'AB_NEGATIVE', name='bloodtype'), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False, comment='Weight in kilograms, minimum 50kg required'),
    sa.Column('height', sa.Float(), nullable=False, comment='Height in centimeters'),
    sa.Column('last_donation_date', sa.Date(), nullable=True),
    sa.Column('first_donation_date', sa.Date(), nullable=True),
    sa.Column('total_donations', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('is_eligible', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('ineligible_until', sa.Date(), nullable=True),
    sa.Column('health_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('hospital_staff',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('DOCTOR', 'NURSE', 'TECHNICIAN', 'ADMIN', name='staffrole'), nullable=True),
    sa.Column('department', sa.Enum('EMERGENCY', 'SURGERY', 'CARDIOLOGY', 'ONCOLOGY', 'PEDIATRICS', 'NEUROLOGY', 'ORTHOPEDICS', 'RADIOLOGY', 'PATHOLOGY', 'ADMINISTRATION', name='department'), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('blood_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('blood_type', sa.Enum('O_POSITIVE', 'O_NEGATIVE', 'A_POSITIVE', 'A_NEGATIVE', 'B_POSITIVE', 'B_NEGATIVE', 'AB_POSITIVE', 'AB_NEGATIVE', name='bloodtype'), nullable=False),
    sa.Column('amount_needed_ml', sa.Integer(), nullable=False, comment='Amount of blood needed in milliliters'),
    sa.Column('patient_info', sa.Text(), nullable=True),
    sa.Column('urgency_level', sa.Integer(), nullable=False, comment='Urgency scale: 1 (low) to 5 (critical)'),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'FULFILLED', 'CANCELED', name='requeststatus'), nullable=False),
    sa.Column('request_date', sa.DateTime(), nullable=False),
    sa.Column('needed_by_date', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.ForeignKeyConstraint(['staff_id'], ['hospital_staff.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('donations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('donor_id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('blood_request_id', sa.Integer(), nullable=True),
    sa.Column('blood_amount_ml', sa.Integer(), nullable=False, comment='Amount of blood donated in milliliters (100-1000ml)'),
    sa.Column('blood_type', sa.Enum('O_POSITIVE', 'O_NEGATIVE', 'A_POSITIVE', 'A_NEGATIVE', 'B_POSITIVE', 'B_NEGATIVE', 'AB_POSITIVE', 'AB_NEGATIVE', name='bloodtype'), nullable=False),
    sa.Column('donation_date', sa.DateTime(), nullable=False),
    sa.Column('status', sa.Enum('SCHEDULED', 'COMPLETED', 'CANCELED', 'REJECTED', name='donationstatus'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['blood_request_id'], ['blood_requests.id'], ),
    sa.ForeignKeyConstraint(['donor_id'], ['donors.id'], ),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('donations')
    op.drop_table('blood_requests')
    op.drop_table('hospital_staff')
    op.drop_table('donors')
    op.drop_table('users')
    op.drop_table('hospitals')
    # ### end Alembic commands ###
