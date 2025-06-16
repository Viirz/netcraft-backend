from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import re
import html
from app.common.db import db
from app.common.models import User, TokenBlocklist, PasswordResetOTP
from app.common.email_service import email_service
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def sanitize_input(value, max_length=None):
    """Sanitize user input"""
    if not isinstance(value, str):
        return value
    
    # Remove potentially dangerous characters
    sanitized = html.escape(value.strip())
    
    if max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_password(password):
    """Validate password requirements: 8-30 chars, uppercase, lowercase, number"""
    if len(password) < 8 or len(password) > 30:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['nickname', 'email', 'password', 'first_name', 'last_name']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate email
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password
        if not validate_password(data['password']):
            return jsonify({'error': 'Password must be 8-30 characters with uppercase, lowercase, and number'}), 400
        
        # Validate nickname length
        if len(data['nickname']) < 3 or len(data['nickname']) > 50:
            return jsonify({'error': 'Nickname must be 3-50 characters'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == data['email']) | (User.nickname == data['nickname'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'User with this email or nickname already exists'}), 409
        
        # Sanitize input
        data['nickname'] = sanitize_input(data.get('nickname', ''), 50)
        data['first_name'] = sanitize_input(data.get('first_name', ''), 100)
        data['last_name'] = sanitize_input(data.get('last_name', ''), 100)
        data['email'] = data.get('email', '').strip().lower()
        data['password'] = sanitize_input(data.get('password', ''))
        
        # Create new user
        user = User(
            nickname=data['nickname'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        token = create_access_token(identity=user.user_ulid)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed for email {data.get('email', 'unknown')}: {str(e)}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = create_access_token(identity=user.user_ulid)
        
        return jsonify({
            'message': 'Login successful',
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Login failed for email {data.get('email', 'unknown')}: {str(e)}")
        return jsonify({'error': 'Login failed'}), 400

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Current password and new password required'}), 400
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Invalid current password'}), 401
        
        if not validate_password(data['new_password']):
            return jsonify({'error': 'New password must be 8-30 characters with uppercase, lowercase, and number'}), 400
        
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password change failed for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Password change failed'}), 400

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email required'}), 400
        
        # Always return success to prevent user enumeration
        user = User.query.filter_by(email=data['email']).first()
        
        if user and email_service.is_configured():
            # Only send email if user exists
            PasswordResetOTP.invalidate_all_user_otps(user.user_ulid)
            otp = PasswordResetOTP(user_ulid=user.user_ulid, expiry_minutes=15)
            db.session.add(otp)
            db.session.commit()
            
            email_service.send_otp_email(
                to_email=user.email,
                first_name=user.first_name,
                otp_code=otp.otp_code
            )
        
        # Always return the same response
        return jsonify({
            'message': 'If an account with this email exists, a password reset code has been sent.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password reset request failed: {str(e)}")
        return jsonify({'error': 'Password reset request failed. Please try again.'}), 400
    
@auth_bp.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'otp_code' not in data:
            return jsonify({'error': 'Email and OTP code required'}), 400
        
        # Validate email format
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            return jsonify({'error': 'Invalid email format'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the latest valid OTP for the user
        otp = PasswordResetOTP.get_latest_valid_otp(user.user_ulid)
        
        if not otp:
            return jsonify({'error': 'No valid OTP found. Please request a new one.'}), 400
        
        if otp.otp_code != data['otp_code']:
            return jsonify({'error': 'Invalid OTP code'}), 400
        
        # OTP is valid, don't mark as used yet - just confirm it's correct
        return jsonify({
            'message': 'OTP verified successfully',
            'reset_token_expires_in_minutes': 15
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"OTP verification failed for email {data.get('email', 'unknown')}: {str(e)}")
        return jsonify({'error': 'OTP verification failed'}), 400

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        required_fields = ['email', 'otp_code', 'new_password']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Email, OTP code, and new password required'}), 400
        
        # Validate email format
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate new password
        if not validate_password(data['new_password']):
            return jsonify({'error': 'New password must be 8-30 characters with uppercase, lowercase, and number'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the latest valid OTP for the user
        otp = PasswordResetOTP.get_latest_valid_otp(user.user_ulid)
        
        if not otp:
            return jsonify({'error': 'No valid OTP found. Please request a new one.'}), 400
        
        if otp.otp_code != data['otp_code']:
            return jsonify({'error': 'Invalid OTP code'}), 400
        
        # Mark OTP as used
        otp.mark_as_used()
        
        # Update user password
        user.set_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password reset failed for email {data.get('email', 'unknown')}: {str(e)}")
        return jsonify({'error': 'Password reset failed'}), 400

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        current_user_id = get_jwt_identity()
        token = get_jwt()
        jti = token['jti']
        token_type = token['type']
        
        # Calculate token expiration time
        exp_timestamp = token['exp']
        expires_at = datetime.fromtimestamp(exp_timestamp)
        
        # Add token to blocklist
        TokenBlocklist.add_token_to_blocklist(
            jti=jti,
            token_type=token_type,
            user_id=current_user_id,
            expires_at=expires_at
        )
        
        return jsonify({'message': 'Successfully logged out'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Logout failed for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 400