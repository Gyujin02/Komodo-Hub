from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.core import User, Membership, Role, AccessCode
from app.models.school import Program, Activity, ProgramAssignment, Submission
from app.models.community import Message
from app.utils import role_required, org_required, get_active_org_id, get_active_role, log_action
from datetime import datetime
import hashlib

school_bp = Blueprint('school', __name__, url_prefix='/school')

SCHOOL_ROLES = ('school_admin', 'school_principal', 'teacher', 'student')
TEACHER_ROLES = ('school_admin', 'teacher')
ADMIN_ROLES = ('school_admin', 'school_principal')


@school_bp.route('/dashboard')
@login_required
@role_required(*SCHOOL_ROLES)
@org_required
def dashboard():
    org_id = get_active_org_id()
    role = get_active_role()

    if role == 'student':
        assignments = ProgramAssignment.query.filter_by(organization_id=org_id, assignee_user_id=current_user.id).all()
        submissions = Submission.query.filter_by(organization_id=org_id, student_user_id=current_user.id).all()
        return render_template('school/student_dashboard.html', assignments=assignments, submissions=submissions)

    programs = Program.query.filter_by(organization_id=org_id).all()
    students = db.session.query(User).join(Membership).join(Role).filter(
        Membership.organization_id == org_id,
        Role.name == 'student',
        Membership.state == 'active'
    ).all()
    submissions = Submission.query.filter_by(organization_id=org_id).all()
    return render_template('school/teacher_dashboard.html', programs=programs, students=students, submissions=submissions)


@school_bp.route('/programs/create', methods=['GET', 'POST'])
@login_required
@role_required(*TEACHER_ROLES)
@org_required
def create_program():
    org_id = get_active_org_id()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        program = Program(organization_id=org_id, title=title, description=description, created_by=current_user.id)
        db.session.add(program)
        db.session.commit()
        log_action(org_id, current_user.id, 'ACTIVITY_CREATE', target_id=program.id)
        flash('Program created!')
        return redirect(url_for('school.dashboard'))

    return render_template('school/create_program.html')


@school_bp.route('/programs/<int:program_id>/activities/create', methods=['GET', 'POST'])
@login_required
@role_required(*TEACHER_ROLES)
@org_required
def create_activity(program_id):
    org_id = get_active_org_id()
    program = Program.query.filter_by(id=program_id, organization_id=org_id).first_or_404()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        due_str = request.form.get('due_at', '')
        due_at = datetime.strptime(due_str, '%Y-%m-%d') if due_str else None

        activity = Activity(organization_id=org_id, program_id=program_id, title=title, content=content, due_at=due_at, created_by=current_user.id)
        db.session.add(activity)
        db.session.commit()
        log_action(org_id, current_user.id, 'ACTIVITY_CREATE', target_id=activity.id)
        flash('Activity created!')
        return redirect(url_for('school.dashboard'))

    return render_template('school/create_activity.html', program=program)


@school_bp.route('/programs/<int:program_id>/assign/<int:user_id>', methods=['POST'])
@login_required
@role_required(*TEACHER_ROLES)
@org_required
def assign_program(program_id, user_id):
    org_id = get_active_org_id()
    student = User.query.get_or_404(user_id)

    if not Membership.query.filter_by(user_id=user_id, organization_id=org_id, state='active').first():
        flash('User not in this organisation.')
        return redirect(url_for('school.dashboard'))

    if ProgramAssignment.query.filter_by(organization_id=org_id, program_id=program_id, assignee_user_id=user_id).first():
        flash('Already assigned.')
        return redirect(url_for('school.dashboard'))

    db.session.add(ProgramAssignment(organization_id=org_id, program_id=program_id, assignee_user_id=user_id, assigned_by=current_user.id))
    db.session.commit()
    log_action(org_id, current_user.id, 'ACTIVITY_ASSIGN', target_id=program_id)
    flash('Program assigned to ' + student.display_name)
    return redirect(url_for('school.dashboard'))


@school_bp.route('/activities/<int:activity_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('student')
@org_required
def submit_activity(activity_id):
    org_id = get_active_org_id()
    activity = Activity.query.filter_by(id=activity_id, organization_id=org_id).first_or_404()
    existing = Submission.query.filter_by(organization_id=org_id, activity_id=activity_id, student_user_id=current_user.id).first()

    if existing and existing.state != 'draft':
        flash('Already submitted.')
        return redirect(url_for('school.dashboard'))

    if request.method == 'POST':
        content = request.form['content']

        if existing:
            existing.content = content
            existing.state = 'submitted'
            existing.submitted_at = datetime.utcnow()
        else:
            db.session.add(Submission(organization_id=org_id, activity_id=activity_id, student_user_id=current_user.id, content=content, state='submitted', submitted_at=datetime.utcnow()))

        db.session.commit()
        log_action(org_id, current_user.id, 'SUBMISSION_CREATE', target_id=activity_id)
        flash('Submitted!')
        return redirect(url_for('school.dashboard'))

    return render_template('school/submit_activity.html', activity=activity)


@school_bp.route('/submissions/<int:sub_id>/grade', methods=['POST'])
@login_required
@role_required(*TEACHER_ROLES)
@org_required
def grade_submission(sub_id):
    org_id = get_active_org_id()
    sub = Submission.query.filter_by(id=sub_id, organization_id=org_id).first_or_404()
    sub.grade = request.form['grade']
    sub.feedback = request.form['feedback']
    sub.state = 'graded'
    db.session.commit()
    log_action(org_id, current_user.id, 'SUBMISSION_GRADE', target_id=sub_id)
    flash('Feedback saved.')
    return redirect(url_for('school.submissions'))


@school_bp.route('/submissions')
@login_required
@role_required(*SCHOOL_ROLES)
@org_required
def submissions():
    org_id = get_active_org_id()
    role = get_active_role()

    if role == 'student':
        subs = Submission.query.filter_by(organization_id=org_id, student_user_id=current_user.id).all()
    elif role == 'teacher':
        subs = Submission.query.join(Activity).filter(Submission.organization_id == org_id, Activity.created_by == current_user.id).all()
    else:
        subs = Submission.query.filter_by(organization_id=org_id).all()

    return render_template('school/submissions.html', submissions=subs, role=role)


@school_bp.route('/messages')
@login_required
@role_required(*SCHOOL_ROLES)
@org_required
def messages():
    org_id = get_active_org_id()
    msgs = Message.query.filter(
        Message.organization_id == org_id,
        db.or_(Message.sender_user_id == current_user.id, Message.receiver_user_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()

    peers = db.session.query(User).join(Membership).filter(
        Membership.organization_id == org_id,
        Membership.state == 'active',
        User.id != current_user.id
    ).all()
    return render_template('school/messages.html', messages=msgs, peers=peers)


@school_bp.route('/messages/send', methods=['POST'])
@login_required
@role_required(*SCHOOL_ROLES)
@org_required
def send_message():
    org_id = get_active_org_id()
    receiver_id = request.form.get('receiver_id', type=int)
    body = request.form['body']

    if not Membership.query.filter_by(user_id=receiver_id, organization_id=org_id, state='active').first():
        flash('Recipient not in your organisation.')
        return redirect(url_for('school.messages'))

    db.session.add(Message(organization_id=org_id, sender_user_id=current_user.id, receiver_user_id=receiver_id, body=body))
    db.session.commit()
    flash('Message sent.')
    return redirect(url_for('school.messages'))


@school_bp.route('/accesscodes')
@login_required
@role_required(*ADMIN_ROLES)
@org_required
def accesscodes():
    org_id = get_active_org_id()
    codes = AccessCode.query.filter_by(organization_id=org_id).all()
    roles = Role.query.filter(Role.name.in_(['teacher', 'student'])).all()
    return render_template('school/accesscodes.html', codes=codes, roles=roles)


@school_bp.route('/accesscodes/create', methods=['POST'])
@login_required
@role_required(*ADMIN_ROLES)
@org_required
def create_accesscode():
    org_id = get_active_org_id()
    role_id = request.form.get('role_id', type=int)
    max_uses = request.form.get('max_uses', type=int, default=1)
    expires_str = request.form.get('expires_at', '')
    raw_code = request.form['code']

    role = Role.query.get(role_id)
    if not role or role.name not in ('teacher', 'student'):
        flash('Invalid role.')
        return redirect(url_for('school.accesscodes'))

    hashed = hashlib.sha256(raw_code.encode()).hexdigest()
    expires_at = datetime.strptime(expires_str, '%Y-%m-%d') if expires_str else None

    db.session.add(AccessCode(organization_id=org_id, code=hashed, role_id=role_id, max_uses=max_uses, expires_at=expires_at, created_by=current_user.id))
    db.session.commit()
    log_action(org_id, current_user.id, 'ACCESSCODE_CREATE')
    flash('Access code created! Share with users: ' + raw_code)
    return redirect(url_for('school.accesscodes'))
