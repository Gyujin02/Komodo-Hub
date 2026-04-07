from functools import wraps
from flask import abort, session
from flask_login import current_user
from app.extensions import db
from app.models.core import AuditLog


def get_active_role():
    from app.models.core import Membership
    org_id = session.get('active_org_id')
    if not org_id or not current_user.is_authenticated:
        return None
    m = Membership.query.filter_by(user_id=current_user.id, organization_id=org_id, state='active').first()
    return m.role.name if m else None


def get_active_org_id():
    return session.get('active_org_id')


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if get_active_role() not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def org_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        from app.models.core import Membership
        org_id = session.get('active_org_id')
        m = Membership.query.filter_by(user_id=current_user.id, organization_id=org_id, state='active').first()
        if not m or not m.organization.is_approved:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def log_action(org_id, actor_id, action, target_id=None):
    entry = AuditLog(organization_id=org_id, actor_user_id=actor_id, action=action, target_id=target_id)
    db.session.add(entry)
    db.session.commit()
