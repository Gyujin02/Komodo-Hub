from app.extensions import db
from datetime import datetime


class Program(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default='org_internal')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='programs')
    creator = db.relationship('User', foreign_keys=[created_by])
    activities = db.relationship('Activity', back_populates='program')
    assignments = db.relationship('ProgramAssignment', back_populates='program')


class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    due_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    program = db.relationship('Program', back_populates='activities')
    creator = db.relationship('User', foreign_keys=[created_by])
    submissions = db.relationship('Submission', back_populates='activity')


class ProgramAssignment(db.Model):
    __tablename__ = 'program_assignments'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    assignee_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('organization_id', 'program_id', 'assignee_user_id', name='u_prog_assign'),
    )

    program = db.relationship('Program', back_populates='assignments')
    assignee = db.relationship('User', foreign_keys=[assignee_user_id])
    assigner = db.relationship('User', foreign_keys=[assigned_by])


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    student_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text)
    file_url = db.Column(db.String(500))
    state = db.Column(db.String(20), nullable=False, default='draft')
    submitted_at = db.Column(db.DateTime, nullable=True)
    grade = db.Column(db.String(50))
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('organization_id', 'activity_id', 'student_user_id', name='u_submission'),
    )

    activity = db.relationship('Activity', back_populates='submissions')
    student = db.relationship('User', foreign_keys=[student_user_id])
