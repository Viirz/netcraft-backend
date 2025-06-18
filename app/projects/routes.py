from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.common.db import db
from app.common.models import Project
import html
import json
import logging

projects_bp = Blueprint('projects', __name__)
logger = logging.getLogger(__name__)

def sanitize_project_input(data):
    """Sanitize project input data"""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[html.escape(key)] = html.escape(value)
            elif isinstance(value, dict):
                sanitized[html.escape(key)] = sanitize_project_input(value)
            elif isinstance(value, list):
                sanitized[html.escape(key)] = [
                    html.escape(item) if isinstance(item, str) else item 
                    for item in value
                ]
            else:
                sanitized[html.escape(key)] = value
        return sanitized
    return data

@projects_bp.route('/my-projects', methods=['GET'])
@jwt_required()
def get_my_projects():
    try:
        current_user_id = get_jwt_identity()
        
        # Query all projects for the current user, ordered by creation date (newest first)
        projects = Project.query.filter_by(owner_ulid=current_user_id)\
                                .order_by(Project.created_at.desc())\
                                .all()
        
        # Convert projects to dict format without the data column
        projects_data = [project.to_dict(include_data=False) for project in projects]
        
        return jsonify({
            'projects': projects_data,
            'count': len(projects_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve projects for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve projects'}), 400

@projects_bp.route('/save', methods=['POST'])
@jwt_required()
def save_project():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Project name is required'}), 400
        
        # Enhanced validation
        name = str(data['name']).strip()
        if len(name) < 1 or len(name) > 100:
            return jsonify({'error': 'Project name must be 1-100 characters'}), 400
        
        # Sanitize inputs
        sanitized_name = html.escape(name)
        sanitized_data = sanitize_project_input(data.get('data', {}))
        
        # Validate JSON data size to prevent DoS
        try:
            json_str = json.dumps(sanitized_data)
            if len(json_str) > 1048576:  # 1MB limit
                return jsonify({'error': 'Project data too large (max 1MB)'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid project data format'}), 400
        
        # Create new project
        project = Project(
            name=sanitized_name,
            data=sanitized_data,
            owner_ulid=current_user_id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project saved successfully',
            'project_ulid': project.project_ulid
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save project for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Failed to save project'}), 400

@projects_bp.route('/<project_ulid>', methods=['GET'])
@jwt_required()
def get_project(project_ulid):
    try:
        current_user_id = get_jwt_identity()
        
        # Validate ULID format first
        if not is_valid_ulid(project_ulid):
            return jsonify({'error': 'Invalid project identifier'}), 400
        
        project = Project.query.get(project_ulid)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if user owns the project
        if project.owner_ulid != current_user_id:
            return jsonify({'error': 'Project not found'}), 404  # Don't reveal existence
        
        return jsonify(project.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve project {project_ulid} for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve project'}), 400

def is_valid_ulid(ulid_str):
    """Validate ULID format"""
    try:
        from ulid import ULID
        ULID.from_str(ulid_str)
        return True
    except (ValueError, TypeError):
        return False

@projects_bp.route('/<project_ulid>', methods=['DELETE'])
@jwt_required()
def delete_project(project_ulid):
    try:
        current_user_id = get_jwt_identity()
        
        project = Project.query.get(project_ulid)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if user owns the project
        if project.owner_ulid != current_user_id:
            return jsonify({'error': 'Access denied - not project owner'}), 403
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': 'Project deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete project {project_ulid} for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete project'}), 400