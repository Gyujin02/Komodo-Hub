from flask import Flask
from app.extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'komodo-hub-secret-2025'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///komodo_hub.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    from app.models.core import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth.routes import auth_bp
    from app.school.routes import school_bp
    from app.community.routes import community_bp
    from app.foundation.routes import foundation_bp
    from app.main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(school_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(foundation_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        _seed()

    return app


def _seed():
    from app.models.core import Organization, User, Role, Membership, AuditLog
    from app.models.school import Program, Activity, ProgramAssignment, Submission
    from app.models.community import Species, SightingReport
    from app.models.library import Library
    from werkzeug.security import generate_password_hash
    from datetime import datetime

    if Role.query.first():
        return

    roles = {}
    for name, desc in [
        ('foundation_admin', 'Platform administrator'),
        ('compliance_officer', 'Compliance and audit role'),
        ('school_principal', 'School registration and subscription'),
        ('school_admin', 'School user and access code management'),
        ('teacher', 'Creates and manages activities'),
        ('student', 'Accesses assigned programs and activities'),
        ('community_admin', 'Community management and access codes'),
        ('community_member', 'Community participation'),
        ('public_user', 'Public access only')
    ]:
        r = Role(name=name, description=desc)
        db.session.add(r)
        roles[name] = r
    db.session.flush()

    # Organisations from case study
    foundation_org = Organization(name='Yayasan Komodo', type='foundation', state='active')
    school_org = Organization(name='Ujung Raya Primary School', type='school', state='active')
    community_org = Organization(name='#SaveOurAnimals Community', type='community', state='active')
    pending_org = Organization(name='Banteng Conservation School', type='school', state='pending')
    db.session.add_all([foundation_org, school_org, community_org, pending_org])
    db.session.flush()

    users = {}
    for email, name in [
        ('admin@yayasankomodo.org', 'Asnawi'),
        ('principal@ujungraya.sch.id', 'Khairunnisa'),
        ('admin@ujungraya.sch.id', 'Ayu Lestari'),
        ('teacher@ujungraya.sch.id', 'Bintang Akbar'),
        ('student@ujungraya.sch.id', 'Sari Dewi'),
        ('chairman@saveouranimals.org', 'Besoeki Rachmat')
    ]:
        u = User(email=email, password_hash=generate_password_hash('password123'), display_name=name)
        db.session.add(u)
        users[email] = u
    db.session.flush()

    for org, user, role_name in [
        (foundation_org, users['admin@yayasankomodo.org'], 'foundation_admin'),
        (school_org, users['principal@ujungraya.sch.id'], 'school_principal'),
        (school_org, users['admin@ujungraya.sch.id'], 'school_admin'),
        (school_org, users['teacher@ujungraya.sch.id'], 'teacher'),
        (school_org, users['student@ujungraya.sch.id'], 'student'),
        (community_org, users['chairman@saveouranimals.org'], 'community_admin')
    ]:
        db.session.add(Membership(
            organization_id=org.id,
            user_id=user.id,
            role_id=roles[role_name].id,
            state='active',
            joined_at=datetime.utcnow()
        ))
    db.session.flush()

    # Species from case study
    species_list = []
    for common, scientific, status, desc in [
        ('Komodo Dragon', 'Varanus komodoensis', 'Vulnerable',
         'The world\'s largest living lizard, found on Komodo Island and nearby islands.'),
        ('Sumatran Tiger', 'Panthera tigris sumatrae', 'Critically Endangered',
         'The smallest tiger subspecies, found only on the Indonesian island of Sumatra.'),
        ('Javan Rhinoceros', 'Rhinoceros sondaicus', 'Critically Endangered',
         'One of the rarest large mammals on Earth, found in Ujung Kulon National Park.'),
        ('Orangutan', 'Pongo pygmaeus', 'Critically Endangered',
         'One of humanity\'s closest relatives, facing habitat loss in Borneo and Sumatra.'),
        ('Bali Myna', 'Leucopsar rothschildi', 'Critically Endangered',
         'A striking white bird endemic to Bali, severely threatened by poaching.'),
        ('Javan Eagle', 'Nisaetus bartelsi', 'Endangered',
         'A rare bird of prey endemic to Java, threatened by deforestation.'),
        ('Tarsius', 'Tarsius tarsier', 'Vulnerable',
         'One of the world\'s smallest primates, found in Sulawesi and nearby islands.'),
        ('Celebes Crested Macaque', 'Macaca nigra', 'Critically Endangered',
         'A striking black macaque found in North Sulawesi, threatened by hunting and habitat loss.')
    ]:
        s = Species(common_name=common, scientific_name=scientific,
                    conservation_status=status, description=desc)
        db.session.add(s)
        species_list.append(s)
    db.session.flush()

    # Program from case study
    program = Program(
        organization_id=school_org.id,
        title='Javan Rhinoceros Conservation Program',
        description='A school conservation program focused on the Javan Rhinoceros in Ujung Kulon National Park. Students learn to observe, document, and report endangered species sightings.',
        created_by=users['teacher@ujungraya.sch.id'].id,
        visibility='org_internal'
    )
    db.session.add(program)
    db.session.flush()

    act1 = Activity(
        organization_id=school_org.id,
        program_id=program.id,
        title='Javan Rhinoceros Field Observation',
        content='Visit Ujung Kulon National Park and document any signs of Javan Rhinoceros activity. Record footprints, feeding areas, and any direct sightings. Submit a written report with your observations.',
        created_by=users['teacher@ujungraya.sch.id'].id
    )
    act2 = Activity(
        organization_id=school_org.id,
        program_id=program.id,
        title='Conservation Essay: Why is the Javan Rhinoceros Endangered?',
        content='Write a 500-word essay explaining the main threats to the Javan Rhinoceros population and what conservation efforts are being made to protect them.',
        created_by=users['teacher@ujungraya.sch.id'].id
    )
    act3 = Activity(
        organization_id=school_org.id,
        program_id=program.id,
        title='Species Sighting Log',
        content='Keep a daily log for one week of any endangered species sightings near your school or home. Record the species, location, time, and what the animal was doing.',
        created_by=users['teacher@ujungraya.sch.id'].id
    )
    db.session.add_all([act1, act2, act3])
    db.session.flush()

    db.session.add(ProgramAssignment(
        organization_id=school_org.id,
        program_id=program.id,
        assignee_user_id=users['student@ujungraya.sch.id'].id,
        assigned_by=users['teacher@ujungraya.sch.id'].id
    ))

    db.session.add(Submission(
        organization_id=school_org.id,
        activity_id=act1.id,
        student_user_id=users['student@ujungraya.sch.id'].id,
        content='I observed Javan Rhino tracks near the eastern fence of the park. The footprint was approximately 40cm wide. I also noticed fresh mud wallowing near the river bank.',
        state='graded',
        grade='A',
        feedback='Excellent field observation! Your measurements were very precise and your descriptions were detailed. Well done!',
        submitted_at=datetime.utcnow()
    ))

    # Library items
    db.session.add(Library(
        organization_id=school_org.id,
        type='report',
        title='Javan Rhino Sighting Report - Ujung Kulon 2025',
        content='Compiled field observations by students of Ujung Raya Primary School during the conservation program. Multiple rhino tracks recorded near the eastern trail.',
        visibility='public',
        created_by=users['teacher@ujungraya.sch.id'].id
    ))

    # Sighting reports from community
    db.session.add(SightingReport(
        organization_id=community_org.id,
        species_id=species_list[2].id,  # Javan Rhinoceros
        reported_by=users['chairman@saveouranimals.org'].id,
        title='Javan Rhino spotted near Ciujung River',
        location='Ciujung River, Ujung Kulon National Park',
        notes='Spotted a lone adult Javan Rhinoceros drinking at the river bank at dusk. The animal appeared healthy and undisturbed.',
        status='reviewed'
    ))
    db.session.add(SightingReport(
        organization_id=community_org.id,
        species_id=species_list[1].id,  # Sumatran Tiger
        reported_by=users['chairman@saveouranimals.org'].id,
        title='Sumatran Tiger tracks found in Gunung Leuser',
        location='Gunung Leuser National Park, North Sumatra',
        notes='Fresh tiger tracks found along the forest trail. Tracks suggest a large adult male. Area has been flagged for monitoring.',
        status='pending'
    ))

    db.session.add(AuditLog(
        organization_id=school_org.id,
        actor_user_id=users['admin@ujungraya.sch.id'].id,
        action='ORG_CREATE',
        target_id=school_org.id
    ))

    db.session.commit()
    print('Database seeded with Komodo Hub case study data.')
