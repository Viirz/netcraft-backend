from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.common.db import db
from app.common.models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        # Get the current authenticated user ID from JWT
        current_user_id = get_jwt_identity()
        
        # Find the current user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Return user information excluding password and user_ulid
        user_data = {
            'nickname': user.nickname,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user'}), 400