"""
Authentication API Routes using Flask-RESTX
Provides Admin, Agency, and Client authentication endpoints
"""

import uuid
from flask import request
from flask_restx import Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, Agency
from app.extensions import db, api

# Create namespace with /v1 prefix
auth_ns = api.namespace('v1/auth', description='Authentication operations')

# Define models for Swagger documentation
login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

auth_response_model = api.model('AuthResponse', {
    'access_token': fields.String(description='JWT access token'),
    'role': fields.String(description='User role (admin, agency, client)'),
    'msg': fields.String(description='Response message')
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})


@auth_ns.route('/admin/login')
class AdminLogin(Resource):
    @auth_ns.doc('admin_login', security=[])
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Success', auth_response_model)
    @auth_ns.response(400, 'Bad Request', error_model)
    @auth_ns.response(401, 'Unauthorized', error_model)
    def post(self):
        """Admin login endpoint - returns JWT token"""
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            auth_ns.abort(400, "Email and password required")

        user = User.query.filter_by(email=data['email'], role='admin').first()
        if not user or not user.check_password(data['password']):
            auth_ns.abort(401, "Invalid credentials")

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"sub": str(user.id), "role": user.role}
        )
        return {"access_token": access_token, "role": user.role}, 200


@auth_ns.route('/agency/login')
class AgencyLogin(Resource):
    @auth_ns.doc('agency_login', security=[])
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Success', auth_response_model)
    @auth_ns.response(400, 'Bad Request', error_model)
    @auth_ns.response(401, 'Unauthorized', error_model)
    def post(self):
        """Agency login endpoint - returns JWT token"""
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            auth_ns.abort(400, "Email and password required")

        user = User.query.filter_by(email=data['email'], role='agency').first()
        if not user or not user.check_password(data['password']):
            auth_ns.abort(401, "Invalid credentials")

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"sub": str(user.id), "role": user.role}
        )
        return {"access_token": access_token, "role": user.role}, 200


@auth_ns.route('/client/login')
class ClientLogin(Resource):
    @auth_ns.doc('client_login', security=[])
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Success', auth_response_model)
    @auth_ns.response(400, 'Bad Request', error_model)
    @auth_ns.response(401, 'Unauthorized', error_model)
    def post(self):
        """Client login endpoint - returns JWT token"""
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            auth_ns.abort(400, "Email and password required")

        user = User.query.filter_by(email=data['email'], role='client').first()
        if not user or not user.check_password(data['password']):
            auth_ns.abort(401, "Invalid credentials")

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"sub": str(user.id), "role": user.role}
        )
        return {"access_token": access_token, "role": user.role}, 200


@auth_ns.route('/client/register')
class ClientRegister(Resource):
    @auth_ns.doc('client_register', security=[])
    @auth_ns.expect(login_model)
    @auth_ns.response(201, 'Created', auth_response_model)
    @auth_ns.response(400, 'Bad Request', error_model)
    @auth_ns.response(409, 'Conflict', error_model)
    def post(self):
        """Client registration endpoint - creates account and returns JWT"""
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            auth_ns.abort(400, "Email and password required")

        if User.query.filter_by(email=data['email']).first():
            auth_ns.abort(409, "Email already registered")

        user = User(email=data['email'], role='client')
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"sub": str(user.id), "role": user.role}
        )
        return {"access_token": access_token, "role": user.role}, 201


@auth_ns.route('/agency/claim/<agency_id>')
class ClaimAgency(Resource):
    @auth_ns.doc('claim_agency', security=[])
    @auth_ns.expect(login_model)
    @auth_ns.response(201, 'Created', auth_response_model)
    @auth_ns.response(400, 'Bad Request', error_model)
    @auth_ns.response(404, 'Not Found', error_model)
    @auth_ns.response(409, 'Conflict', error_model)
    def post(self, agency_id):
        """Claim approved agency account with email verification"""
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            auth_ns.abort(400, "Email and password required")

        agency = Agency.query.filter_by(agency_id=agency_id, status='approved').first()
        if not agency:
            auth_ns.abort(404, "Approved agency not found")

        if agency.email != data['email']:
            auth_ns.abort(400, "Email does not match agency registration")

        if User.query.filter_by(email=data['email']).first():
            auth_ns.abort(409, "Email already registered")

        user = User(email=data['email'], role='agency', agency_id=agency.agency_id)
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"sub": str(user.id), "role": user.role}
        )
        return {"access_token": access_token, "role": user.role}, 201
