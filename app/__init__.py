from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from app.config import Config
from app.common.db import db
from app.common.models import TokenBlocklist, PasswordResetOTP
import time
import logging
import threading

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # JWT token in blocklist loader
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return TokenBlocklist.is_jti_blocklisted(jti)
    
    # JWT revoked token callback
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has been revoked'}), 401
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.projects.routes import projects_bp
    from app.users.routes import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'message': 'API is running'}), 200
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'NETCRAFT API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth/*',
                'projects': '/api/projects/*',
                'users': '/api/users/*'
            }
        }), 200
    
    # Enhanced cleanup scheduler function
    def cleanup_expired_data():
        """Periodically clean up expired tokens and OTPs from database"""
        with app.app_context():
            try:
                # Clean up expired tokens
                tokens_cleaned = TokenBlocklist.cleanup_expired_tokens()
                if tokens_cleaned > 0:
                    logger.info(f"Cleaned up {tokens_cleaned} expired tokens from blocklist")
                
                # Clean up expired OTPs
                otps_cleaned = PasswordResetOTP.cleanup_expired_otps()
                if otps_cleaned > 0:
                    logger.info(f"Cleaned up {otps_cleaned} expired OTPs")
                    
            except Exception as e:
                logger.error(f"Error cleaning up expired data: {e}")
    
    def start_cleanup_scheduler():
        """Start the cleanup scheduler"""
        def run_cleanup():
            while True:
                time.sleep(3600)  # Run every hour
                cleanup_expired_data()
        
        cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
        cleanup_thread.start()
        logger.info("Data cleanup scheduler started")
    
    # Create tables with retry logic
    def create_tables_with_retry(max_retries=30, delay=2):
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    db.create_all()
                    logger.info("Database tables created successfully")
                    return True
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Failed to connect to database after all retries")
                    raise
        return False
    
    # Initialize database
    create_tables_with_retry()
    
    # Start cleanup scheduler
    start_cleanup_scheduler()
    
    return app