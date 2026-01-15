import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, Agency
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return {"error": "Email and password required"}, 400

    user = User.query.filter_by(email=data['email'], role='admin').first()
    if not user or not user.check_password(data['password']):
        return {"error": "Invalid credentials"}, 401

    access_token = create_access_token(identity=user.id, additional_claims={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "role": user.role}, 200

@auth_bp.route('/agency/login', methods=['POST'])
def agency_login():
    """Agency login endpoint"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return {"error": "Email and password required"}, 400

    user = User.query.filter_by(email=data['email'], role='agency').first()
    if not user or not user.check_password(data['password']):
        return {"error": "Invalid credentials"}, 401

    access_token = create_access_token(identity=user.id, additional_claims={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "role": user.role}, 200

@auth_bp.route('/agency/claim/<agency_id>', methods=['POST'])
def claim_agency(agency_id):
    """Claim approved agency account"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return {"error": "Email and password required"}, 400

    # Find approved agency by agency_id
    agency = Agency.query.filter_by(agency_id=agency_id, status='approved').first()
    if not agency:
        return {"error": "Approved agency not found"}, 404

    # Check if email matches
    if agency.email != data['email']:
        return {"error": "Email does not match agency registration"}, 400

    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return {"error": "Email already registered"}, 409

    # Create user account
    user = User(email=data['email'], role='agency', agency_id=agency.agency_id)
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id, additional_claims={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "role": user.role}, 201



@auth_bp.route('/client/login', methods=['POST'])
def client_login():
    """Client login endpoint"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return {"error": "Email and password required"}, 400

    user = User.query.filter_by(email=data['email'], role='client').first()
    if not user or not user.check_password(data['password']):
        return {"error": "Invalid credentials"}, 401

    access_token = create_access_token(identity=user.id, additional_claims={
        'sub': str(user.id),
        'role': 'client'
    })
    return {"access_token": access_token, "role": user.role}, 200

@auth_bp.route('/client/register', methods=['POST'])
def client_register():
    """Client registration endpoint"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return {"error": "Email and password required"}, 400

    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return {"error": "Email already registered"}, 409

    user = User(email=data['email'], role='client')
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id, additional_claims={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "role": user.role}, 201
