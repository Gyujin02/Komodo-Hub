from app.extensions import db
from datetime import datetime


class Species(db.Model):
    __tablename__ = 'species'

    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(150), nullable=False)
    scientific_name = db.Column(db.String(200), unique=True, nullable=False)
    conservation_status = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sighting_reports = db.relationship('SightingReport', back_populates='species')


class SightingReport(db.Model):
    __tablename__ = 'sighting_reports'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='sighting_reports')
    species = db.relationship('Species', back_populates='sighting_reports')
    reporter = db.relationship('User', foreign_keys=[reported_by])


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    sender_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='messages')
    sender = db.relationship('User', foreign_keys=[sender_user_id])
    receiver = db.relationship('User', foreign_keys=[receiver_user_id])
