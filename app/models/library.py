from app.extensions import db
from datetime import datetime


class Library(db.Model):
    __tablename__ = 'library'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default='org_internal')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', back_populates='library_items')
    creator = db.relationship('User', foreign_keys=[created_by])
