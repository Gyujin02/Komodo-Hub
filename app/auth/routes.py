from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.core import User, Organization, Role, Membership, AccessCode
from app.utils import log_action
from datetime import datetime
import hashlib

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.')
            return render_template('auth/login.html')

        membership = Membership.query.filter_by(user_id=user.id, state='active').first()

        if not membership:
            flash('No active membership found.')
            return render_template('auth/login.html')

        school_roles = ('school_principal', 'school_admin', 'teacher', 'student')
        if membership.role.name in school_roles:
            if not membership.organization.is_approved:
                flash('Your school is pending approval.')
                return render_template('auth/login.html')

        login_user(user)
        session['active_org_id'] = membership.organization_id
        log_action(membership.organization_id, user.id, 'LOGIN_SUCCESS')

        role = membership.role.name
        if role in ('foundation_admin', 'compliance_officer'):
            return redirect(url_for('foundation.dashboard'))
        elif role in ('school_admin', 'school_principal', 'teacher', 'student'):
            return redirect(url_for('school.dashboard'))
        elif role in ('community_admin', 'community_member'):
            return redirect(url_for('community.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register/school', methods=['GET', 'POST'])
def register_school():
    if request.method == 'POST':
        school_name = request.form['school_name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return render_template('auth/register_school.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return render_template('auth/register_school.html')

        org = Organization(name=school_name, type='school', state='pending')
        db.session.add(org)
        db.session.flush()

        user = User(email=email, password_hash=generate_password_hash(password), display_name=school_name)
        db.session.add(user)
        db.session.flush()

        role = Role.query.filter_by(name='school_admin').first()
        db.session.add(Membership(organization_id=org.id, user_id=user.id, role_id=role.id, state='active', joined_at=datetime.utcnow()))
        db.session.commit()

        log_action(org.id, user.id, 'ORG_CREATE', target_id=org.id)
        flash('School registered! Waiting for approval.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_school.html')


@auth_bp.route('/register/community', methods=['GET', 'POST'])
def register_community():
    if request.method == 'POST':
        org_name = request.form['org_name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return render_template('auth/register_community.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return render_template('auth/register_community.html')

        org = Organization(name=org_name, type='community', state='active')
        db.session.add(org)
        db.session.flush()

        user = User(email=email, password_hash=generate_password_hash(password), display_name=org_name)
        db.session.add(user)
        db.session.flush()

        role = Role.query.filter_by(name='community_admin').first()
        db.session.add(Membership(organization_id=org.id, user_id=user.id, role_id=role.id, state='active', joined_at=datetime.utcnow()))
        db.session.commit()

        log_action(org.id, user.id, 'ORG_CREATE', target_id=org.id)
        flash('Community registered!')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_community.html')


@auth_bp.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        display_name = request.form['display_name']
        raw_code = request.form['access_code']

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return render_template('auth/join.html')

        hashed = hashlib.sha256(raw_code.encode()).hexdigest()
        code = AccessCode.query.filter_by(code=hashed).first()

        if not code or not code.is_valid:
            flash('Invalid or expired access code.')
            return render_template('auth/join.html')

        user = User(email=email, password_hash=generate_password_hash(password), display_name=display_name)
        db.session.add(user)
        db.session.flush()

        db.session.add(Membership(organization_id=code.organization_id, user_id=user.id, role_id=code.role_id, state='active', joined_at=datetime.utcnow()))

        code.used_count += 1
        if code.used_count >= code.max_uses:
            code.state = 'exhausted'

        db.session.commit()
        log_action(code.organization_id, user.id, 'USER_CREATE', target_id=user.id)
        flash('Account created! You can now sign in.')
        return redirect(url_for('auth.login'))

    return render_template('auth/join.html')
