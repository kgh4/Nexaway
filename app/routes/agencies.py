import os
import uuid
import smtplib
from email.mime.text import MIMEText
from flask import Blueprint, request, abort, current_app
from werkzeug.utils import secure_filename
from app.services.agency_service import AgencyService
from app.models import PendingAgency, Agency
from app.extensions import db

agencies_bp = Blueprint('agencies', __name__)

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@nexaway.com'
    msg['To'] = to
    try:
        server = smtplib.SMTP('localhost')
        server.sendmail('noreply@nexaway.com', to, msg.as_string())
        server.quit()
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")

@agencies_bp.route('/agencies', methods=['GET'])
def get_agencies():
    agencies = AgencyService.get_agencies_sorted_by_trust()
    return {
        'data': agencies,
        'total': len(agencies)
    }

@agencies_bp.route('/agencies', methods=['POST'])
def create_agency():
    data = request.get_json()
    if not data:
        return {"error": "JSON payload required"}, 400

    try:
        result = AgencyService.add_agency(data)
        return result, 201
    except Exception as e:
        return {"error": str(e)}, 400

@agencies_bp.route('/agencies/<int:id>', methods=['GET'])
def get_agency(id):
    agencies = AgencyService.get_agencies_sorted_by_trust()
    if not (1 <= id <= len(agencies)):
        return {"error": f"Agency #{id} not found"}, 404

    return agencies[id-1]

@agencies_bp.route('/agencies/<tax_id>', methods=['GET'])
def get_agency_by_tax_id(tax_id):
    agencies = AgencyService.load_csv()
    agency = next((a for a in agencies if a['tax_id'] == tax_id), None)
    if not agency:
        return {"error": "Agency not found"}, 404

    return agency

@agencies_bp.route('/agencies/search', methods=['GET'])
def search_agencies():
    governorate = request.args.get('governorate')
    min_trust = request.args.get('min_trust', type=int)

    agencies = AgencyService.get_agencies_sorted_by_trust()

    filtered = agencies
    if governorate:
        filtered = [a for a in filtered if a.get('governorate', '').lower() == governorate.lower()]
    if min_trust:
        filtered = [a for a in filtered if a.get('trust_score', 0) >= min_trust]

    return {
        'items': filtered,
        'total': len(filtered),
        'filters': {
            'governorate': governorate,
            'min_trust': min_trust
        }
    }

@agencies_bp.route('/agencies/stats', methods=['GET'])
def get_agency_stats():
    agencies = AgencyService.load_csv()

    # Governorate stats
    stats = {}
    for agency in agencies:
        gov = agency.get('governorate', 'Unknown')
        stats[gov] = stats.get(gov, 0) + 1

    # Calculations
    total = len(agencies)
    avg_trust = sum(float(a.get('trust_score', 50)) for a in agencies) / total if total > 0 else 0

    # Get top-rated agencies
    top_rated_limit = request.args.get('top_rated_limit', 5, type=int)
    top_rated_agencies = AgencyService.get_agencies_sorted_by_trust()[:top_rated_limit]

    return {
        'stats': stats,
        'total': total,
        'avg_trust': round(avg_trust, 1),
        'top_governorate': max(stats.items(), key=lambda x: x[1], default=('None', 0)),
        'highest_rated_agencies': top_rated_agencies
    }



@agencies_bp.route('/agencies/<tax_id>', methods=['PATCH', 'DELETE'])
def agency_ops(tax_id):
    if request.method == 'PATCH':
        return AgencyService.update_agency(tax_id, request.json)
    if request.method == 'DELETE':
        AgencyService.delete_agency(tax_id)
        return '', 204

@agencies_bp.route('/agencies/register', methods=['POST'])
def register_agency():
    """Register new agency with file upload"""
    # Check if multipart form data
    if 'license_image' not in request.files:
        return {"error": "license_image file required"}, 400

    # Get form data
    agency_tax_id = request.form.get('agency_tax_id')
    agency_name = request.form.get('agency_name')
    owner_name = request.form.get('owner_name')
    owner_phone = request.form.get('owner_phone')
    owner_email = request.form.get('owner_email')
    governorate = request.form.get('governorate')
    address = request.form.get('address')
    license_image = request.files['license_image']

    # DEBUG PRINTS - REMOVE AFTER FIX
    print("=" * 50)
    print("FORM DATA RECEIVED:")
    print(dict(request.form))
    print("FILES RECEIVED:")
    print(list(request.files.keys()))
    print("LICENSE FILENAME:", request.files['license_image'].filename if 'license_image' in request.files else "MISSING")
    print("AGENCY_TAX_ID:", request.form.get('agency_tax_id'))
    print("AGENCY_NAME:", request.form.get('agency_name'))
    print("GOVERNORATE:", request.form.get('governorate'))
    print("ADDRESS:", request.form.get('address'))
    print("=" * 50)

    # Validate required fields
    if not all([agency_tax_id, agency_name, owner_name, owner_phone, owner_email, governorate, address]):
        return {"error": "All fields required"}, 400

    # Validate RNE format
    if not validate_rne_format(agency_tax_id):
        return {"error": "Invalid RNE format (must be 8 digits)"}, 400

    # Validate file
    if license_image.filename == '':
        return {"error": "No file selected"}, 400

    if license_image and not allowed_file(license_image.filename):
        return {"error": "Invalid file type"}, 400

    # Check file size (5MB limit)
    license_image.seek(0, os.SEEK_END)
    file_size = license_image.tell()
    license_image.seek(0)
    if file_size > 5 * 1024 * 1024:
        return {"error": "File too large (max 5MB)"}, 413

    # Generate pending ID
    pending_id = f"P-{uuid.uuid4().hex[:8].upper()}"

    # Save file
    filename = f"{pending_id}.jpg"
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    license_image.save(file_path)

    # Create pending record
    pending = PendingAgency(
        pending_id=pending_id,
        agency_tax_id=agency_tax_id,
        company_name=agency_name,
        email=owner_email,
        phone=owner_phone,
        governorate=governorate,
        address=address
    )
    pending.license_image_url = f"/static/uploads/{filename}"

    db.session.add(pending)
    db.session.commit()

    # Send email to admin
    send_email(
        'admin@nexaway.com',
        'New Agency Registration Pending',
        f'New agency registration: {agency_name} (RNE: {agency_tax_id})'
    )

    return {
        "pending_id": pending_id,
        "status": "pending"
    }, 201

@agencies_bp.route('/admin/pending_agencies', methods=['GET'])
def get_pending_agencies():
    """List pending agencies with pagination"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    query = PendingAgency.query.filter_by(status='pending')
    total = query.count()
    pendings = query.offset((page-1)*limit).limit(limit).all()

    return {
        'data': [p.to_dict() for p in pendings],
        'total': total,
        'page': page,
        'limit': limit
    }

@agencies_bp.route('/admin/pending/<pending_id>/approve', methods=['POST'])
def approve_pending_agency(pending_id):
    """Approve pending agency"""
    pending = PendingAgency.query.filter_by(pending_id=pending_id, status='pending').first()
    if not pending:
        return {"error": "Pending agency not found"}, 404

    # Create agency record
    agency = Agency(
        tax_id=pending.agency_tax_id,
        company_name=pending.company_name,
        official_name=pending.official_name,
        email=pending.email,
        phone=pending.phone,
        address=pending.address,
        governorate=pending.governorate,
        website=pending.website,
        sectors=pending.sectors,
        tourism_license=pending.tourism_license,
        registry_number=pending.registry_number,
        verification_status='verified',
        status='active',
        source='registration'
    )

    db.session.add(agency)
    db.session.delete(pending)
    db.session.commit()

    # Send approval email
    send_email(
        pending.email,
        'Agency Registration Approved',
        f'Your agency {pending.company_name} has been approved! Login email: {pending.email}'
    )

    return {"status": "approved"}, 200

@agencies_bp.route('/admin/pending/<pending_id>/reject', methods=['POST'])
def reject_pending_agency(pending_id):
    """Reject pending agency"""
    data = request.get_json() or {}
    reason = data.get('reason', 'No reason provided')

    pending = PendingAgency.query.filter_by(pending_id=pending_id, status='pending').first()
    if not pending:
        return {"error": "Pending agency not found"}, 404

    # Delete pending record
    db.session.delete(pending)
    db.session.commit()

    # Send rejection email
    send_email(
        pending.email,
        'Agency Registration Rejected',
        f'Your agency registration for {pending.company_name} has been rejected. Reason: {reason}'
    )

    return {"status": "rejected"}, 200

@agencies_bp.route('/agencies/top-rated', methods=['GET'])
def get_top_rated_agencies():
    """Get top-rated agencies (by trust score)"""
    limit = request.args.get('limit', 10, type=int)

    agencies = AgencyService.get_agencies_sorted_by_trust()[:limit]

    return {
        'data': agencies,
        'total': len(agencies),
        'message': 'Trusted by us, Rated by clients!'
    }

@agencies_bp.route('/agencies/top-rated/governorate/<governorate>', methods=['GET'])
def get_top_rated_agencies_by_governorate(governorate):
    """Get top-rated agencies in a specific governorate"""
    limit = request.args.get('limit', 10, type=int)

    agencies = AgencyService.get_agencies_sorted_by_trust()
    filtered = [a for a in agencies if a.get('governorate', '').lower() == governorate.lower()][:limit]

    return {
        'data': filtered,
        'total': len(filtered),
        'governorate': governorate,
        'message': 'Trusted by us, Rated by clients!'
    }

@agencies_bp.route('/debug/routes', methods=['GET'])
def debug_routes():
    return {'routes': [str(rule) for rule in current_app.url_map.iter_rules()]}

def validate_rne_format(rne):
    """Validate RNE format (must be 8 digits)"""
    return rne.isdigit() and len(rne) == 8

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


