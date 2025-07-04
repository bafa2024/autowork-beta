#!/usr/bin/env python3
"""
Project Management API Server
Provides REST API endpoints for the project management dashboard
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# Import project management system
from project_management import ProjectManager, ProjectStatus, TaskStatus, Priority

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize project manager
freelancer_token = os.environ.get('FREELANCER_OAUTH_TOKEN')
if not freelancer_token:
    logger.error("FREELANCER_OAUTH_TOKEN not found in environment variables")
    exit(1)

project_manager = ProjectManager(
    freelancer_token=freelancer_token,
    redis_url=os.environ.get('REDIS_URL')
)

@app.route('/')
def index():
    """Serve the project dashboard"""
    try:
        with open('project_dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Project dashboard HTML file not found", 404

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard data"""
    try:
        data = project_manager.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({
            'error': str(e),
            'metrics': {
                'active_projects': 0,
                'total_hours_tracked': 0,
                'completion_rate': 0
            },
            'active_projects': [],
            'today_tasks': [],
            'upcoming_deadlines': []
        }), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        from project_management import ManagedProject
        projects = project_manager.session.query(ManagedProject).all()
        return jsonify([project_manager._project_summary(p) for p in projects])
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/sync', methods=['POST'])
def sync_projects():
    """Sync projects from Freelancer"""
    try:
        imported_projects = project_manager.fetch_and_import_awarded_projects()
        return jsonify({
            'success': True,
            'imported_count': len(imported_projects),
            'message': f'Imported {len(imported_projects)} new projects'
        })
    except Exception as e:
        logger.error(f"Error syncing projects: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/projects/import', methods=['POST'])
def import_project():
    """Import a specific project by ID"""
    try:
        data = request.get_json()
        project_id = data.get('freelancer_project_id')
        
        if not project_id:
            return jsonify({
                'success': False,
                'error': 'Project ID is required'
            }), 400
        
        # Check if project already exists
        from project_management import ManagedProject
        existing = project_manager.session.query(ManagedProject).filter(
            ManagedProject.freelancer_project_id == project_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Project already exists in system'
            }), 400
        
        # Import the project
        project = project_manager.import_awarded_project(project_id)
        
        if project:
            return jsonify({
                'success': True,
                'project': project_manager._project_summary(project),
                'message': f'Project {project_id} imported successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to import project {project_id}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error importing project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get specific project details"""
    try:
        from project_management import ManagedProject
        project = project_manager.session.query(ManagedProject).filter(
            ManagedProject.id == project_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get detailed project data
        project_data = project_manager._project_summary(project)
        
        # Add tasks
        project_data['tasks'] = [project_manager._task_summary(task) for task in project.tasks]
        
        # Add recent communications
        recent_comms = project_manager.session.query(project_manager.Communication).filter(
            project_manager.Communication.project_id == project_id
        ).order_by(project_manager.Communication.timestamp.desc()).limit(5).all()
        
        project_data['recent_communications'] = [{
            'subject': comm.subject,
            'type': comm.message_type,
            'timestamp': comm.timestamp.isoformat(),
            'content': comm.content[:100] + '...' if len(comm.content) > 100 else comm.content
        } for comm in recent_comms]
        
        # Add risk assessment
        risk_assessment = project_manager.assess_project_risk(project_id)
        project_data['risk_assessment'] = risk_assessment
        
        return jsonify(project_data)
        
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/status', methods=['PUT'])
def update_project_status(project_id):
    """Update project status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        # Validate status
        try:
            status_enum = ProjectStatus(new_status)
        except ValueError:
            return jsonify({'error': f'Invalid status: {new_status}'}), 400
        
        success = project_manager.update_project_status(project_id, status_enum)
        
        if success:
            return jsonify({'success': True, 'message': 'Project status updated'})
        else:
            return jsonify({'error': 'Failed to update project status'}), 400
            
    except Exception as e:
        logger.error(f"Error updating project status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Update task status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        # Validate status
        try:
            status_enum = TaskStatus(new_status)
        except ValueError:
            return jsonify({'error': f'Invalid status: {new_status}'}), 400
        
        success = project_manager.update_task_status(task_id, status_enum)
        
        if success:
            # Recalculate project progress
            task = project_manager.session.query(project_manager.Task).filter(
                project_manager.Task.id == task_id
            ).first()
            if task:
                project_manager.recalculate_project_progress(task.project_id)
            
            return jsonify({'success': True, 'message': 'Task status updated'})
        else:
            return jsonify({'error': 'Failed to update task status'}), 400
            
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/time', methods=['POST'])
def log_time(project_id):
    """Log time for a project"""
    try:
        data = request.get_json()
        hours = data.get('hours')
        description = data.get('description')
        
        if not hours or not description:
            return jsonify({'error': 'Hours and description are required'}), 400
        
        if hours <= 0:
            return jsonify({'error': 'Hours must be positive'}), 400
        
        project_manager.log_time(
            project_id=project_id,
            task_id=None,  # Could be made optional
            hours=hours,
            description=description,
            user="Developer"
        )
        
        # Recalculate project progress
        project_manager.recalculate_project_progress(project_id)
        
        return jsonify({'success': True, 'message': 'Time logged successfully'})
        
    except Exception as e:
        logger.error(f"Error logging time: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/report', methods=['GET'])
def get_project_report(project_id):
    """Generate project report"""
    try:
        from project_management import ManagedProject
        project = project_manager.session.query(ManagedProject).filter(
            ManagedProject.id == project_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Generate report
        report_text = project_manager.generate_project_report(project_id)
        
        # Get project data for the report
        project_data = project_manager._project_summary(project)
        tasks = [project_manager._task_summary(task) for task in project.tasks]
        
        return jsonify({
            'success': True,
            'project_title': project.title,
            'status': project.status.value,
            'progress': project.progress_percentage,
            'hours_tracked': project.hours_tracked,
            'deadline': project.deadline.isoformat() if project.deadline else None,
            'tasks': tasks,
            'recent_activity': report_text
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/client-update', methods=['POST'])
def send_client_update(project_id):
    """Send client update"""
    try:
        data = request.get_json()
        update_type = data.get('type', 'progress')
        
        project_manager.send_client_update(project_id, update_type)
        
        return jsonify({'success': True, 'message': 'Client update sent successfully'})
        
    except Exception as e:
        logger.error(f"Error sending client update: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from project_management import ManagedProject
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'project_count': project_manager.session.query(ManagedProject).count()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sdlc/analyze', methods=['POST'])
def analyze_project_sdlc():
    """Analyze project description and generate SDLC documents"""
    try:
        data = request.get_json()
        project_description = data.get('project_description', '')
        project_title = data.get('project_title', 'Project')
        budget = data.get('budget', {})
        ai_provider = data.get('ai_provider', 'openai')
        
        if not project_description.strip():
            return jsonify({
                'success': False,
                'error': 'Project description is required'
            }), 400
        
        # Import and initialize SDLC service
        from auto_sdlc_service import AutoSDLCService
        
        sdlc_service = AutoSDLCService(ai_provider=ai_provider)
        
        # Analyze project
        analysis = sdlc_service.analyze_project(project_description, budget)
        
        # Generate SRS
        srs = sdlc_service.generate_srs(project_description, analysis, project_title)
        
        # Generate Design
        design = sdlc_service.generate_design(srs, analysis)
        
        # Generate Implementation Plan
        plan = sdlc_service.generate_implementation_plan(design, analysis, analysis.estimated_hours)
        
        # Convert to JSON-serializable format
        from dataclasses import asdict
        
        result = {
            'success': True,
            'analysis': asdict(analysis),
            'srs': asdict(srs),
            'design': asdict(design),
            'implementation_plan': asdict(plan),
            'summary': {
                'project_type': analysis.project_type,
                'complexity': analysis.complexity,
                'estimated_hours': analysis.estimated_hours,
                'technologies': analysis.technologies,
                'key_features': analysis.key_features,
                'risks': analysis.risks
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing project SDLC: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sdlc/export', methods=['POST'])
def export_sdlc_documents():
    """Export SDLC documents in various formats"""
    try:
        data = request.get_json()
        srs_data = data.get('srs', {})
        design_data = data.get('design', {})
        plan_data = data.get('implementation_plan', {})
        export_format = data.get('format', 'json')
        
        # Import SDLC service
        from auto_sdlc_service import AutoSDLCService, SRSDocument, DesignDocument, ImplementationPlan
        
        sdlc_service = AutoSDLCService()
        
        # Reconstruct objects from data
        srs = SRSDocument(**srs_data)
        design = DesignDocument(**design_data)
        plan = ImplementationPlan(**plan_data)
        
        # Export documents
        files = sdlc_service.export_documents(srs, design, plan, format=export_format)
        
        return jsonify({
            'success': True,
            'files': files,
            'message': f'Documents exported in {export_format} format'
        })
        
    except Exception as e:
        logger.error(f"Error exporting SDLC documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '127.0.0.1')
    
    logger.info(f"Starting Project Management API on {host}:{port}")
    logger.info(f"Dashboard will be available at: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=True) 