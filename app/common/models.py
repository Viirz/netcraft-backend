from datetime import datetime, timedelta
from ulid import ULID
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from app.common.db import db

class User(db.Model):
    __tablename__ = 'users'
    
    user_ulid = db.Column(db.String(26), primary_key=True, default=lambda: str(ULID()))
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='owner', lazy=True, cascade='all, delete-orphan')
    password_reset_otps = db.relationship('PasswordResetOTP', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'user_ulid': self.user_ulid,
            'nickname': self.nickname,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_sensitive:
            data['password'] = self.password_hash
        return data

class Project(db.Model):
    __tablename__ = 'projects'
    
    project_ulid = db.Column(db.String(26), primary_key=True, default=lambda: str(ULID()))
    name = db.Column(db.String(100), nullable=False)
    data = db.Column(db.JSON)
    owner_ulid = db.Column(db.String(26), db.ForeignKey('users.user_ulid'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_data=True):
        data = {
            'project_ulid': self.project_ulid,
            'name': self.name,
            'owner_ulid': self.owner_ulid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_data:
            data['data'] = self.data
        return data

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.String(26), db.ForeignKey('users.user_ulid'), nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<TokenBlocklist {self.jti}>'
    
    @staticmethod
    def is_jti_blocklisted(jti):
        """Check if a JWT ID is in the blocklist"""
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None
    
    @staticmethod
    def add_token_to_blocklist(jti, token_type, user_id, expires_at):
        """Add a token to the blocklist"""
        blocklist_token = TokenBlocklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(blocklist_token)
        db.session.commit()
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from the blocklist"""
        expired_tokens = TokenBlocklist.query.filter(
            TokenBlocklist.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        
        db.session.commit()
        return len(expired_tokens)

class PasswordResetOTP(db.Model):
    __tablename__ = 'password_reset_otps'
    
    id = db.Column(db.Integer, primary_key=True)
    user_ulid = db.Column(db.String(26), db.ForeignKey('users.user_ulid'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    is_used = db.Column(db.Boolean, default=False)
    
    def __init__(self, user_ulid, expiry_minutes=15):
        self.user_ulid = user_ulid
        self.otp_code = self.generate_otp()
        self.expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    @staticmethod
    def get_latest_valid_otp(user_ulid):
        """Get the latest valid OTP for a user"""
        return PasswordResetOTP.query.filter_by(
            user_ulid=user_ulid,
            is_used=False
        ).filter(
            PasswordResetOTP.expires_at > datetime.utcnow()
        ).order_by(
            PasswordResetOTP.created_at.desc()
        ).first()
    
    @staticmethod
    def invalidate_all_user_otps(user_ulid):
        """Mark all existing OTPs for a user as used"""
        otps = PasswordResetOTP.query.filter_by(
            user_ulid=user_ulid,
            is_used=False
        ).all()
        
        for otp in otps:
            otp.mark_as_used()
    
    @staticmethod
    def cleanup_expired_otps():
        """Remove expired OTPs from the database"""
        expired_otps = PasswordResetOTP.query.filter(
            PasswordResetOTP.expires_at < datetime.utcnow()
        ).all()
        
        for otp in expired_otps:
            db.session.delete(otp)
        
        db.session.commit()
        return len(expired_otps)