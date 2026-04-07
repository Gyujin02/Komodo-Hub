from flask import Blueprint, render_template
from app.models.core import Organization
from app.models.community import Species, SightingReport
from app.models.library import Library

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    stats = {
        'schools': Organization.query.filter_by(type='school', state='active').count(),
        'communities': Organization.query.filter_by(type='community', state='active').count(),
        'sightings': SightingReport.query.count(),
        'species': Species.query.count()
    }
    return render_template('shared/index.html', stats=stats, featured=Species.query.all())


@main_bp.route('/schools')
def schools():
    schools = Organization.query.filter_by(type='school', state='active').all()
    return render_template('shared/schools.html', schools=schools)


@main_bp.route('/communities')
def communities():
    communities = Organization.query.filter_by(type='community', state='active').all()
    return render_template('shared/communities.html', communities=communities)


@main_bp.route('/library')
def public_library():
    items = Library.query.filter_by(visibility='public').all()
    return render_template('shared/library.html', items=items)


@main_bp.route('/species')
def species():
    return render_template('shared/species.html', species=Species.query.all())
