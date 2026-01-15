from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != role or not isinstance(claims.get('sub'), str):
                return jsonify({"msg": "Invalid token"}), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def client_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'client':
            return jsonify({"error": "Client access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
