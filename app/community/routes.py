from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.core import User, Membership, Role, AccessCode, Organization
from app.models.community import Species, SightingReport
from app.models.library import Library
from app.utils import role_required, get_active_org_id, log_action
from datetime import datetime
import hashlib

community_bp = Blueprint('community', __name__, url_prefix='/community')

COMM_ROLES = ('community_admin', 'community_member')


@community_bp.route('/dashboard')
@login_required
@role_required(*COMM_ROLES)
def dashboard():
    org_id = get_active_org_id()
    reports = SightingReport.query.filter_by(organization_id=org_id).order_by(SightingReport.created_at.desc()).all()
    species_list = Species.query.all()
    schools = Organization.query.filter_by(type='school', state='active').all()
    return render_template('community/dashboard.html', reports=reports, species_list=species_list, schools=schools)


@community_bp.route('/sightings/report', methods=['GET', 'POST'])
@login_required
@role_required(*COMM_ROLES)
def report_sighting():
    org_id = get_active_org_id()

    if request.method == 'POST':
        title = request.form['title']
        species_id = request.form.get('species_id', type=int)
        location = request.form.get('location', '')
        notes = request.form.get('notes', '')

        if not Species.query.get(species_id):
            flash('Invalid species.')
            return redirect(url_for('community.report_sighting'))

        db.session.add(SightingReport(organization_id=org_id, species_id=species_id, reported_by=current_user.id, title=title, location=location, notes=notes))
        db.session.commit()
        log_action(org_id, current_user.id, 'CONTENT_CREATE')
        flash('Sighting report submitted!')
        return redirect(url_for('community.dashboard'))

    return render_template('community/report_sighting.html', species_list=Species.query.all())


@community_bp.route('/library')
@login_required
@role_required(*COMM_ROLES)
def library():
    org_id = get_active_org_id()
    items = Library.query.filter_by(organization_id=org_id).all()
    return render_template('community/library.html', items=items)


@community_bp.route('/library/add', methods=['POST'])
@login_required
@role_required('community_admin')
def add_library_item():
    org_id = get_active_org_id()
    title = request.form['title']
    content = request.form['content']
    item_type = request.form.get('type', 'article')

    db.session.add(Library(organization_id=org_id, type=item_type, title=title, content=content, visibility='public', created_by=current_user.id))
    db.session.commit()
    log_action(org_id, current_user.id, 'CONTENT_CREATE')
    flash('Added to library!')
    return redirect(url_for('community.library'))


@community_bp.route('/accesscodes')
@login_required
@role_required('community_admin')
def accesscodes():
    org_id = get_active_org_id()
    codes = AccessCode.query.filter_by(organization_id=org_id).all()
    roles = Role.query.filter(Role.name.in_(['community_member'])).all()
    return render_template('community/accesscodes.html', codes=codes, roles=roles)


@community_bp.route('/accesscodes/create', methods=['POST'])
@login_required
@role_required('community_admin')
def create_accesscode():
    org_id = get_active_org_id()
    role_id = request.form.get('role_id', type=int)
    max_uses = request.form.get('max_uses', type=int, default=1)
    expires_str = request.form.get('expires_at', '')
    raw_code = request.form['code']

    hashed = hashlib.sha256(raw_code.encode()).hexdigest()
    expires_at = datetime.strptime(expires_str, '%Y-%m-%d') if expires_str else None

    db.session.add(AccessCode(organization_id=org_id, code=hashed, role_id=role_id, max_uses=max_uses, expires_at=expires_at, created_by=current_user.id))
    db.session.commit()
    log_action(org_id, current_user.id, 'ACCESSCODE_CREATE')
    flash('Access code created! Share with users: ' + raw_code)
    return redirect(url_for('community.accesscodes'))
