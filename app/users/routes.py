from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.common.db import db
from app.common.models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/<user_ulid>', methods=['GET'])
@jwt_required()
def get_user(user_ulid):
    try:
        # Get the current authenticated user
        current_user_id = get_jwt_identity()
        
        # Find the requested user
        user = User.query.get(user_ulid)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Return public user information (excluding sensitive data)
        return jsonify(user.to_dict(include_sensitive=False)), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user'}), 400