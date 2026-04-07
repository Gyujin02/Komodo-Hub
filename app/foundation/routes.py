from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.core import Organization, User, AuditLog
from app.models.community import SightingReport
from app.models.school import Program, Activity, Submission
from app.utils import role_required, get_active_org_id, log_action

foundation_bp = Blueprint('foundation', __name__, url_prefix='/foundation')

FOUNDATION_ROLES = ('foundation_admin', 'compliance_officer')


@foundation_bp.route('/dashboard')
@login_required
@role_required(*FOUNDATION_ROLES)
def dashboard():
    pending = Organization.query.filter_by(state='pending').all()
    all_orgs = Organization.query.order_by(Organization.created_at.desc()).all()
    stats = {
        'total_schools': Organization.query.filter_by(type='school').count(),
        'approved_schools': Organization.query.filter_by(type='school', state='active').count(),
        'pending_count': len(pending),
        'communities': Organization.query.filter_by(type='community').count(),
        'total_users': User.query.count(),
        'total_submissions': Submission.query.count(),
        'total_sightings': SightingReport.query.count(),
        'audit_count': AuditLog.query.count()
    }
    return render_template('foundation/dashboard.html', pending=pending, all_orgs=all_orgs, stats=stats)


@foundation_bp.route('/approve/<int:org_id>', methods=['POST'])
@login_required
@role_required('foundation_admin')
def approve_org(org_id):
    org = Organization.query.get_or_404(org_id)
    org.state = 'active'
    db.session.commit()
    flash(org.name + ' approved.')
    return redirect(url_for('foundation.dashboard'))


@foundation_bp.route('/reject/<int:org_id>', methods=['POST'])
@login_required
@role_required('foundation_admin')
def reject_org(org_id):
    org = Organization.query.get_or_404(org_id)
    org.state = 'rejected'
    db.session.commit()
    flash(org.name + ' rejected.')
    return redirect(url_for('foundation.dashboard'))


@foundation_bp.route('/schools')
@login_required
@role_required(*FOUNDATION_ROLES)
def schools():
    schools = Organization.query.filter_by(type='school').all()
    return render_template('foundation/schools.html', schools=schools)


@foundation_bp.route('/communities')
@login_required
@role_required(*FOUNDATION_ROLES)
def communities():
    communities = Organization.query.filter_by(type='community').all()
    return render_template('foundation/communities.html', communities=communities)


@foundation_bp.route('/users')
@login_required
@role_required(*FOUNDATION_ROLES)
def users():
    all_users = User.query.all()
    return render_template('foundation/users.html', users=all_users)


@foundation_bp.route('/audit')
@login_required
@role_required(*FOUNDATION_ROLES)
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template('foundation/audit_log.html', logs=logs)


@foundation_bp.route('/business-dashboard')
@login_required
@role_required(*FOUNDATION_ROLES)
def business_dashboard():
    stats = {
        'total_orgs': Organization.query.filter_by(state='active').count(),
        'total_sightings': SightingReport.query.count(),
        'total_submissions': Submission.query.count(),
        'total_programs': Program.query.count(),
        'total_activities': Activity.query.count()
    }
    sightings_by_species = db.session.execute(
        db.text('SELECT s.common_name, COUNT(sr.id) as count FROM species s LEFT JOIN sighting_reports sr ON sr.species_id = s.id GROUP BY s.id ORDER BY count DESC')
    ).fetchall()
    return render_template('foundation/business_dashboard.html', stats=stats, sightings_by_species=sightings_by_species)
