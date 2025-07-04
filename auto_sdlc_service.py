#!/usr/bin/env python3
"""
Auto SDLC (Software Development Life Cycle) Service
Automatically analyzes project descriptions and generates SRS, design docs, and implementation plans
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
from dataclasses import dataclass, asdict
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class ProjectAnalysis:
    """Data class for project analysis results"""
    project_type: str
    complexity: str
    estimated_hours: int
    technologies: List[str]
    key_features: List[str]
    risks: List[str]
    
@dataclass
class SRSDocument:
    """Software Requirements Specification document structure"""
    project_title: str
    overview: str
    scope: str
    functional_requirements: List[Dict[str, str]]
    non_functional_requirements: List[Dict[str, str]]
    user_stories: List[Dict[str, str]]
    acceptance_criteria: List[str]
    constraints: List[str]
    assumptions: List[str]
    
@dataclass
class DesignDocument:
    """System design document structure"""
    architecture_type: str
    components: List[Dict[str, str]]
    data_models: List[Dict[str, str]]
    api_endpoints: List[Dict[str, str]]
    technology_stack: Dict[str, List[str]]
    security_considerations: List[str]
    scalability_plan: str
    
@dataclass
class ImplementationPlan:
    """Implementation plan with tasks breakdown"""
    phases: List[Dict[str, any]]
    tasks: List[Dict[str, any]]
    milestones: List[Dict[str, str]]
    dependencies: List[Dict[str, str]]
    timeline: Dict[str, any]
    resource_allocation: Dict[str, any]

class AutoSDLCService:
    def __init__(self, ai_provider: str = "openai"):
        """
        Initialize Auto SDLC Service
        
        Args:
            ai_provider: AI service provider ("openai", "anthropic", "gemini")
        """
        self.ai_provider = ai_provider
        self.api_key = self._load_api_key()
        self.headers = self._setup_headers()
        self.templates = self._load_templates()
        
        # Project type patterns
        self.project_patterns = {
            'web_app': ['website', 'web app', 'web application', 'frontend', 'backend', 'full stack'],
            'mobile_app': ['mobile', 'ios', 'android', 'react native', 'flutter'],
            'desktop_app': ['desktop', 'windows', 'mac', 'linux', 'electron'],
            'api': ['api', 'rest', 'graphql', 'microservice', 'backend service'],
            'data_science': ['machine learning', 'ml', 'ai', 'data analysis', 'prediction', 'model'],
            'blockchain': ['blockchain', 'smart contract', 'web3', 'defi', 'nft'],
            'iot': ['iot', 'embedded', 'arduino', 'raspberry pi', 'sensor'],
            'game': ['game', 'unity', 'unreal', 'gaming', 'multiplayer'],
            'automation': ['automation', 'bot', 'scraping', 'workflow', 'integration'],
            'ecommerce': ['ecommerce', 'online store', 'shopping cart', 'payment integration']
        }
        
        # Technology detection patterns
        self.tech_patterns = {
            'languages': {
                'python': ['python', 'django', 'flask', 'fastapi'],
                'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
                'java': ['java', 'spring', 'springboot'],
                'csharp': ['c#', 'csharp', '.net', 'asp.net'],
                'php': ['php', 'laravel', 'symfony', 'wordpress'],
                'ruby': ['ruby', 'rails', 'ruby on rails'],
                'go': ['golang', 'go ', 'gin', 'echo'],
                'rust': ['rust', 'actix', 'rocket'],
                'swift': ['swift', 'ios', 'swiftui'],
                'kotlin': ['kotlin', 'android']
            },
            'databases': {
                'mysql': ['mysql', 'mariadb'],
                'postgresql': ['postgresql', 'postgres', 'psql'],
                'mongodb': ['mongodb', 'mongo', 'nosql'],
                'redis': ['redis', 'cache'],
                'elasticsearch': ['elasticsearch', 'elastic'],
                'firebase': ['firebase', 'firestore']
            },
            'cloud': {
                'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
                'azure': ['azure', 'microsoft cloud'],
                'gcp': ['google cloud', 'gcp', 'google cloud platform'],
                'heroku': ['heroku'],
                'vercel': ['vercel', 'next.js'],
                'netlify': ['netlify']
            }
        }
        
        logging.info(f"✓ Auto SDLC Service initialized with {ai_provider}")
    
    def _load_api_key(self) -> str:
        """Load API key based on provider"""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'gemini': 'GOOGLE_API_KEY'
        }
        
        env_var = key_mapping.get(self.ai_provider)
        api_key = os.environ.get(env_var)
        
        if not api_key:
            # Try loading from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.environ.get(env_var)
            except ImportError:
                pass
        
        if not api_key:
            logging.warning(f"No API key found for {self.ai_provider}. Set {env_var} environment variable.")
            
        return api_key
    
    def _setup_headers(self) -> Dict:
        """Setup API headers based on provider"""
        if self.ai_provider == 'openai':
            return {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        elif self.ai_provider == 'anthropic':
            return {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
        elif self.ai_provider == 'gemini':
            return {
                'Content-Type': 'application/json'
            }
        return {}
    
    def _load_templates(self) -> Dict:
        """Load document templates"""
        templates_file = 'sdlc_templates.json'
        if os.path.exists(templates_file):
            try:
                with open(templates_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Could not load templates: {e}")
        
        # Default templates
        return {
            'srs': {
                'sections': ['overview', 'scope', 'functional_requirements', 'non_functional_requirements'],
                'format': 'structured'
            },
            'design': {
                'sections': ['architecture', 'components', 'data_models', 'api_design'],
                'format': 'technical'
            },
            'implementation': {
                'sections': ['phases', 'tasks', 'milestones', 'timeline'],
                'format': 'gantt'
            }
        }
    
    def analyze_project(self, project_description: str, budget: Dict = None) -> ProjectAnalysis:
        """
        Analyze project description to determine type, complexity, and requirements
        
        Args:
            project_description: The project description text
            budget: Budget information (optional)
            
        Returns:
            ProjectAnalysis object with analysis results
        """
        logging.info("🔍 Analyzing project description...")
        
        # Detect project type
        project_type = self._detect_project_type(project_description)
        
        # Detect technologies
        technologies = self._detect_technologies(project_description)
        
        # Extract key features
        key_features = self._extract_features(project_description)
        
        # Estimate complexity
        complexity = self._estimate_complexity(project_description, len(key_features))
        
        # Estimate hours
        estimated_hours = self._estimate_hours(complexity, project_type, budget)
        
        # Identify risks
        risks = self._identify_risks(project_description, complexity)
        
        analysis = ProjectAnalysis(
            project_type=project_type,
            complexity=complexity,
            estimated_hours=estimated_hours,
            technologies=technologies,
            key_features=key_features,
            risks=risks
        )
        
        logging.info(f"✓ Project analyzed: {project_type} ({complexity} complexity)")
        return analysis
    
    def _detect_project_type(self, description: str) -> str:
        """Detect project type from description"""
        description_lower = description.lower()
        scores = {}
        
        for project_type, keywords in self.project_patterns.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                scores[project_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def _detect_technologies(self, description: str) -> List[str]:
        """Detect technologies mentioned in description"""
        description_lower = description.lower()
        detected_techs = []
        
        for category, tech_groups in self.tech_patterns.items():
            for tech, keywords in tech_groups.items():
                if any(keyword in description_lower for keyword in keywords):
                    detected_techs.append(tech)
        
        return detected_techs
    
    def _extract_features(self, description: str) -> List[str]:
        """Extract key features from description"""
        # Use AI to extract features if API key is available
        if self.api_key:
            features = self._ai_extract_features(description)
            if features:
                return features
        
        # Fallback to pattern matching
        features = []
        feature_patterns = [
            r'(?:feature|functionality|capability|ability to|should be able to|must have|need to)\s+([^.!?]+)',
            r'(?:implement|create|build|develop|design)\s+([^.!?]+)',
            r'(?:-|\*|•)\s*([^.\n]+)'
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            features.extend([match.strip() for match in matches[:5]])
        
        return list(set(features))[:10]  # Return top 10 unique features
    
    def _estimate_complexity(self, description: str, feature_count: int) -> str:
        """Estimate project complexity"""
        word_count = len(description.split())
        
        # Complexity indicators
        complex_keywords = ['complex', 'advanced', 'sophisticated', 'enterprise', 'scalable', 
                          'high-performance', 'distributed', 'microservices', 'machine learning']
        simple_keywords = ['simple', 'basic', 'straightforward', 'minimal', 'prototype', 'mvp']
        
        complex_score = sum(1 for keyword in complex_keywords if keyword in description.lower())
        simple_score = sum(1 for keyword in simple_keywords if keyword in description.lower())
        
        # Calculate complexity
        if complex_score >= 3 or feature_count >= 10 or word_count > 500:
            return 'high'
        elif simple_score >= 2 or feature_count <= 3 or word_count < 100:
            return 'low'
        else:
            return 'medium'
    
    def _estimate_hours(self, complexity: str, project_type: str, budget: Dict = None) -> int:
        """Estimate project hours based on complexity and type"""
        base_hours = {
            'low': {'web_app': 40, 'mobile_app': 60, 'api': 30, 'default': 40},
            'medium': {'web_app': 120, 'mobile_app': 160, 'api': 80, 'default': 100},
            'high': {'web_app': 300, 'mobile_app': 400, 'api': 200, 'default': 250}
        }
        
        hours = base_hours.get(complexity, {}).get(project_type, base_hours[complexity]['default'])
        
        # Adjust based on budget if available
        if budget and 'minimum' in budget:
            min_budget = budget['minimum']
            # Rough estimate: $50-100/hour for development
            budget_hours = min_budget / 75
            hours = (hours + budget_hours) / 2  # Average of estimates
        
        return int(hours)
    
    def _identify_risks(self, description: str, complexity: str) -> List[str]:
        """Identify potential project risks"""
        risks = []
        
        # Common risk patterns
        if 'urgent' in description.lower() or 'asap' in description.lower():
            risks.append("Tight deadline - may affect quality")
        
        if 'integrate' in description.lower() or 'third-party' in description.lower():
            risks.append("Third-party integration dependencies")
        
        if complexity == 'high':
            risks.append("High complexity - requires experienced developers")
        
        if 'real-time' in description.lower():
            risks.append("Real-time requirements - performance critical")
        
        if 'payment' in description.lower() or 'financial' in description.lower():
            risks.append("Financial transactions - security critical")
        
        if not risks:
            risks.append("Standard project risks apply")
        
        return risks
    
    def generate_srs(self, project_description: str, analysis: ProjectAnalysis, 
                     project_title: str = "Project") -> SRSDocument:
        """
        Generate Software Requirements Specification document
        
        Args:
            project_description: Original project description
            analysis: Project analysis results
            project_title: Project title
            
        Returns:
            SRSDocument object
        """
        logging.info("📄 Generating SRS document...")
        
        # Use AI if available
        if self.api_key:
            srs_data = self._ai_generate_srs(project_description, analysis)
            if srs_data:
                return self._parse_srs_response(srs_data, project_title)
        
        # Fallback to template-based generation
        return self._template_generate_srs(project_description, analysis, project_title)
    
    def _template_generate_srs(self, description: str, analysis: ProjectAnalysis, 
                               title: str) -> SRSDocument:
        """Generate SRS using templates"""
        
        # Generate functional requirements from features
        functional_reqs = []
        for i, feature in enumerate(analysis.key_features, 1):
            functional_reqs.append({
                'id': f'FR{i:03d}',
                'description': feature,
                'priority': 'High' if i <= 3 else 'Medium'
            })
        
        # Generate non-functional requirements
        non_functional_reqs = [
            {'id': 'NFR001', 'category': 'Performance', 
             'description': 'System should respond within 2 seconds for all user interactions'},
            {'id': 'NFR002', 'category': 'Security', 
             'description': 'All data transmissions must be encrypted using industry standards'},
            {'id': 'NFR003', 'category': 'Usability', 
             'description': 'Interface should be intuitive and require minimal training'},
            {'id': 'NFR004', 'category': 'Reliability', 
             'description': 'System uptime should be 99.9% excluding scheduled maintenance'}
        ]
        
        # Generate user stories
        user_stories = []
        for i, feature in enumerate(analysis.key_features[:5], 1):
            user_stories.append({
                'id': f'US{i:03d}',
                'story': f'As a user, I want to {feature.lower()} so that I can achieve my goals',
                'acceptance_criteria': [f'{feature} is fully functional', 'User can access this feature easily']
            })
        
        # Create SRS document
        srs = SRSDocument(
            project_title=title,
            overview=f"This document outlines the software requirements for {title}, "
                    f"a {analysis.complexity} complexity {analysis.project_type} project.",
            scope=f"The project encompasses development of a complete {analysis.project_type} "
                  f"with estimated {analysis.estimated_hours} hours of development effort.",
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            user_stories=user_stories,
            acceptance_criteria=[
                "All functional requirements are implemented and tested",
                "System passes all quality assurance tests",
                "Documentation is complete and accurate",
                "User acceptance testing is successful"
            ],
            constraints=[
                f"Project complexity: {analysis.complexity}",
                f"Estimated timeline: {analysis.estimated_hours} hours",
                f"Technologies: {', '.join(analysis.technologies)}"
            ],
            assumptions=[
                "Client will provide timely feedback and clarifications",
                "Required third-party services/APIs will be available",
                "Development environment will be stable"
            ]
        )
        
        logging.info("✓ SRS document generated")
        return srs
    
    def generate_design(self, srs: SRSDocument, analysis: ProjectAnalysis) -> DesignDocument:
        """
        Generate system design document
        
        Args:
            srs: Software Requirements Specification
            analysis: Project analysis results
            
        Returns:
            DesignDocument object
        """
        logging.info("🏗️ Generating design document...")
        
        # Use AI if available
        if self.api_key:
            design_data = self._ai_generate_design(srs, analysis)
            if design_data:
                return self._parse_design_response(design_data)
        
        # Fallback to template-based generation
        return self._template_generate_design(srs, analysis)
    
    def _template_generate_design(self, srs: SRSDocument, analysis: ProjectAnalysis) -> DesignDocument:
        """Generate design document using templates"""
        
        # Determine architecture type
        architecture_map = {
            'web_app': 'Three-tier architecture (Frontend, Backend, Database)',
            'mobile_app': 'Client-Server architecture with REST API',
            'api': 'Microservices architecture with API Gateway',
            'desktop_app': 'Model-View-Controller (MVC) architecture',
            'default': 'Layered architecture'
        }
        architecture = architecture_map.get(analysis.project_type, architecture_map['default'])
        
        # Generate components based on project type
        components = self._generate_components(analysis.project_type)
        
        # Generate data models
        data_models = self._generate_data_models(srs.functional_requirements)
        
        # Generate API endpoints
        api_endpoints = self._generate_api_endpoints(srs.functional_requirements)
        
        # Technology stack
        tech_stack = self._generate_tech_stack(analysis)
        
        # Security considerations
        security = [
            "Implement OAuth 2.0 for authentication",
            "Use HTTPS for all communications",
            "Implement input validation and sanitization",
            "Regular security audits and penetration testing",
            "Implement rate limiting for API endpoints"
        ]
        
        design = DesignDocument(
            architecture_type=architecture,
            components=components,
            data_models=data_models,
            api_endpoints=api_endpoints,
            technology_stack=tech_stack,
            security_considerations=security,
            scalability_plan="Horizontal scaling with load balancing and caching layers"
        )
        
        logging.info("✓ Design document generated")
        return design
    
    def _generate_components(self, project_type: str) -> List[Dict[str, str]]:
        """Generate system components based on project type"""
        base_components = [
            {'name': 'Authentication Service', 'description': 'Handles user authentication and authorization'},
            {'name': 'Database Layer', 'description': 'Manages data persistence and retrieval'},
            {'name': 'Business Logic Layer', 'description': 'Implements core business rules and workflows'}
        ]
        
        type_specific = {
            'web_app': [
                {'name': 'Frontend UI', 'description': 'User interface components and views'},
                {'name': 'API Gateway', 'description': 'Manages API requests and responses'}
            ],
            'mobile_app': [
                {'name': 'Mobile Client', 'description': 'Native mobile application'},
                {'name': 'Push Notification Service', 'description': 'Handles push notifications'},
                {'name': 'Offline Sync Module', 'description': 'Manages offline data synchronization'}
            ],
            'api': [
                {'name': 'API Gateway', 'description': 'Routes and manages API requests'},
                {'name': 'Service Registry', 'description': 'Manages microservice discovery'},
                {'name': 'Message Queue', 'description': 'Handles asynchronous communication'}
            ]
        }
        
        components = base_components.copy()
        components.extend(type_specific.get(project_type, []))
        return components
    
    def _generate_data_models(self, functional_reqs: List[Dict]) -> List[Dict[str, str]]:
        """Generate data models from functional requirements"""
        models = [
            {
                'name': 'User',
                'fields': 'id, username, email, password_hash, created_at, updated_at',
                'relationships': 'Has many: Sessions, Activities'
            },
            {
                'name': 'Session',
                'fields': 'id, user_id, token, expires_at, created_at',
                'relationships': 'Belongs to: User'
            }
        ]
        
        # Add models based on requirements
        for req in functional_reqs[:3]:
            model_name = req['description'].split()[0].capitalize()
            models.append({
                'name': model_name,
                'fields': f'id, name, description, status, created_at, updated_at',
                'relationships': 'Belongs to: User'
            })
        
        return models
    
    def _generate_api_endpoints(self, functional_reqs: List[Dict]) -> List[Dict[str, str]]:
        """Generate API endpoints from functional requirements"""
        endpoints = [
            {'method': 'POST', 'path': '/api/auth/login', 'description': 'User authentication'},
            {'method': 'POST', 'path': '/api/auth/logout', 'description': 'User logout'},
            {'method': 'GET', 'path': '/api/user/profile', 'description': 'Get user profile'}
        ]
        
        # Generate CRUD endpoints for main entities
        for i, req in enumerate(functional_reqs[:3], 1):
            entity = req['description'].split()[0].lower()
            endpoints.extend([
                {'method': 'GET', 'path': f'/api/{entity}s', 'description': f'List all {entity}s'},
                {'method': 'POST', 'path': f'/api/{entity}s', 'description': f'Create new {entity}'},
                {'method': 'GET', 'path': f'/api/{entity}s/{{id}}', 'description': f'Get {entity} by ID'},
                {'method': 'PUT', 'path': f'/api/{entity}s/{{id}}', 'description': f'Update {entity}'},
                {'method': 'DELETE', 'path': f'/api/{entity}s/{{id}}', 'description': f'Delete {entity}'}
            ])
        
        return endpoints
    
    def _generate_tech_stack(self, analysis: ProjectAnalysis) -> Dict[str, List[str]]:
        """Generate recommended technology stack"""
        # Base stack
        stack = {
            'frontend': [],
            'backend': [],
            'database': [],
            'infrastructure': [],
            'tools': []
        }
        
        # Add detected technologies
        for tech in analysis.technologies:
            if tech in ['react', 'vue', 'angular']:
                stack['frontend'].append(tech)
            elif tech in ['python', 'node', 'java', 'php']:
                stack['backend'].append(tech)
            elif tech in ['mysql', 'postgresql', 'mongodb']:
                stack['database'].append(tech)
            elif tech in ['aws', 'azure', 'gcp']:
                stack['infrastructure'].append(tech)
        
        # Add defaults if empty
        if not stack['frontend'] and analysis.project_type in ['web_app', 'mobile_app']:
            stack['frontend'] = ['React', 'Tailwind CSS']
        if not stack['backend']:
            stack['backend'] = ['Node.js', 'Express']
        if not stack['database']:
            stack['database'] = ['PostgreSQL', 'Redis']
        if not stack['infrastructure']:
            stack['infrastructure'] = ['Docker', 'Kubernetes']
        
        stack['tools'] = ['Git', 'Jenkins/GitHub Actions', 'Jest/Pytest', 'Postman']
        
        return stack
    
    def generate_implementation_plan(self, design: DesignDocument, analysis: ProjectAnalysis,
                                   estimated_hours: int) -> ImplementationPlan:
        """
        Generate implementation plan with task breakdown
        
        Args:
            design: Design document
            analysis: Project analysis
            estimated_hours: Total estimated hours
            
        Returns:
            ImplementationPlan object
        """
        logging.info("📋 Generating implementation plan...")
        
        # Use AI if available
        if self.api_key:
            plan_data = self._ai_generate_plan(design, analysis, estimated_hours)
            if plan_data:
                return self._parse_plan_response(plan_data)
        
        # Fallback to template-based generation
        return self._template_generate_plan(design, analysis, estimated_hours)
    
    def _template_generate_plan(self, design: DesignDocument, analysis: ProjectAnalysis,
                               total_hours: int) -> ImplementationPlan:
        """Generate implementation plan using templates"""
        
        # Define phases
        phases = [
            {
                'name': 'Setup & Planning',
                'duration_percent': 10,
                'description': 'Project setup, environment configuration, and detailed planning'
            },
            {
                'name': 'Core Development',
                'duration_percent': 50,
                'description': 'Implementation of core features and functionality'
            },
            {
                'name': 'Integration & Testing',
                'duration_percent': 25,
                'description': 'System integration, testing, and bug fixes'
            },
            {
                'name': 'Deployment & Documentation',
                'duration_percent': 15,
                'description': 'Deployment preparation, documentation, and handover'
            }
        ]
        
        # Calculate phase durations
        for phase in phases:
            phase['hours'] = int(total_hours * phase['duration_percent'] / 100)
            phase['days'] = max(1, phase['hours'] // 8)
        
        # Generate tasks
        tasks = self._generate_tasks(design, phases)
        
        # Generate milestones
        milestones = [
            {
                'name': 'Project Kickoff',
                'deliverable': 'Development environment setup and project plan approved',
                'phase': 'Setup & Planning'
            },
            {
                'name': 'Alpha Release',
                'deliverable': 'Core features implemented and functional',
                'phase': 'Core Development'
            },
            {
                'name': 'Beta Release',
                'deliverable': 'All features complete with testing',
                'phase': 'Integration & Testing'
            },
            {
                'name': 'Production Release',
                'deliverable': 'Final deployment with documentation',
                'phase': 'Deployment & Documentation'
            }
        ]
        
        # Generate timeline
        timeline = {
            'total_hours': total_hours,
            'total_days': max(1, total_hours // 8),
            'total_weeks': max(1, total_hours // 40),
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'phases': phases
        }
        
        # Resource allocation
        resources = {
            'developers': self._calculate_developers_needed(total_hours, analysis.complexity),
            'roles': self._determine_roles(analysis.project_type),
            'tools': design.technology_stack.get('tools', [])
        }
        
        plan = ImplementationPlan(
            phases=phases,
            tasks=tasks,
            milestones=milestones,
            dependencies=self._generate_dependencies(tasks),
            timeline=timeline,
            resource_allocation=resources
        )
        
        logging.info("✓ Implementation plan generated")
        return plan
    
    def _generate_tasks(self, design: DesignDocument, phases: List[Dict]) -> List[Dict]:
        """Generate detailed tasks for each phase"""
        tasks = []
        task_id = 1
        
        # Phase 1: Setup tasks
        setup_tasks = [
            'Set up development environment',
            'Configure version control',
            'Set up CI/CD pipeline',
            'Create project documentation structure',
            'Set up development database'
        ]
        
        for task_name in setup_tasks:
            tasks.append({
                'id': f'T{task_id:03d}',
                'name': task_name,
                'phase': 'Setup & Planning',
                'estimated_hours': phases[0]['hours'] // len(setup_tasks),
                'dependencies': []
            })
            task_id += 1
        
        # Phase 2: Development tasks (from components)
        for component in design.components:
            tasks.append({
                'id': f'T{task_id:03d}',
                'name': f"Implement {component['name']}",
                'phase': 'Core Development',
                'estimated_hours': phases[1]['hours'] // len(design.components),
                'dependencies': ['T001', 'T002']  # Depends on setup
            })
            task_id += 1
        
        # Phase 3: Testing tasks
        test_tasks = [
            'Write unit tests',
            'Perform integration testing',
            'Conduct security testing',
            'User acceptance testing',
            'Performance optimization'
        ]
        
        for task_name in test_tasks:
            tasks.append({
                'id': f'T{task_id:03d}',
                'name': task_name,
                'phase': 'Integration & Testing',
                'estimated_hours': phases[2]['hours'] // len(test_tasks),
                'dependencies': [f'T{i:03d}' for i in range(6, task_id)][:3]  # Depends on some dev tasks
            })
            task_id += 1
        
        # Phase 4: Deployment tasks
        deploy_tasks = [
            'Prepare production environment',
            'Create deployment scripts',
            'Write user documentation',
            'Create admin documentation',
            'Final deployment and handover'
        ]
        
        for task_name in deploy_tasks:
            tasks.append({
                'id': f'T{task_id:03d}',
                'name': task_name,
                'phase': 'Deployment & Documentation',
                'estimated_hours': phases[3]['hours'] // len(deploy_tasks),
                'dependencies': [f'T{task_id-6:03d}']  # Depends on testing
            })
            task_id += 1
        
        return tasks
    
    def _generate_dependencies(self, tasks: List[Dict]) -> List[Dict[str, str]]:
        """Generate task dependencies"""
        dependencies = []
        
        for task in tasks:
            for dep in task.get('dependencies', []):
                dependencies.append({
                    'from': dep,
                    'to': task['id'],
                    'type': 'finish-to-start'
                })
        
        return dependencies
    
    def _calculate_developers_needed(self, total_hours: int, complexity: str) -> int:
        """Calculate number of developers needed"""
        # Assuming 40 hours per week per developer
        weeks = total_hours / 40
        
        if weeks <= 2:
            return 1
        elif weeks <= 4:
            return 2 if complexity == 'high' else 1
        elif weeks <= 12:
            return 3 if complexity == 'high' else 2
        else:
            return 4 if complexity == 'high' else 3
    
    def _determine_roles(self, project_type: str) -> List[str]:
        """Determine required roles based on project type"""
        base_roles = ['Project Manager', 'Backend Developer', 'QA Engineer']
        
        type_specific = {
            'web_app': ['Frontend Developer', 'UI/UX Designer'],
            'mobile_app': ['Mobile Developer', 'UI/UX Designer'],
            'api': ['DevOps Engineer', 'API Architect'],
            'data_science': ['Data Scientist', 'ML Engineer'],
            'blockchain': ['Blockchain Developer', 'Security Auditor']
        }
        
        roles = base_roles.copy()
        roles.extend(type_specific.get(project_type, []))
        return list(set(roles))
    
    # AI Integration Methods (if API key available)
    
    def _ai_extract_features(self, description: str) -> Optional[List[str]]:
        """Use AI to extract features from description"""
        if not self.api_key:
            return None
        
        prompt = f"""Extract the key features and requirements from this project description. 
        List only the main features, one per line:
        
        {description}
        
        Features:"""
        
        try:
            response = self._call_ai_api(prompt)
            if response:
                features = [line.strip() for line in response.split('\n') if line.strip()]
                return features[:10]
        except Exception as e:
            logging.warning(f"AI feature extraction failed: {e}")
        
        return None
    
    def _ai_generate_srs(self, description: str, analysis: ProjectAnalysis) -> Optional[Dict]:
        """Use AI to generate SRS content"""
        if not self.api_key:
            return None
        
        prompt = f"""Generate a Software Requirements Specification (SRS) for this project:
        
        Project Type: {analysis.project_type}
        Complexity: {analysis.complexity}
        Description: {description}
        
        Provide the following sections in JSON format:
        1. Overview
        2. Scope
        3. Functional Requirements (list of 5-8 items)
        4. Non-Functional Requirements (list of 4-6 items)
        5. User Stories (list of 3-5 stories)
        6. Acceptance Criteria (list of 4-5 criteria)
        
        Format as valid JSON."""
        
        try:
            response = self._call_ai_api(prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logging.warning(f"AI SRS generation failed: {e}")
        
        return None
    
    def _ai_generate_design(self, srs: SRSDocument, analysis: ProjectAnalysis) -> Optional[Dict]:
        """Use AI to generate design document"""
        if not self.api_key:
            return None
        
        prompt = f"""Generate a system design for this project:
        
        Project Type: {analysis.project_type}
        Requirements Summary: {srs.overview}
        Key Features: {', '.join([req['description'] for req in srs.functional_requirements[:5]])}
        
        Provide the following in JSON format:
        1. Architecture type and description
        2. Main components (list of 5-8 components with descriptions)
        3. Data models (list of 4-6 models with fields)
        4. API endpoints (list of 8-10 endpoints)
        5. Technology recommendations
        
        Format as valid JSON."""
        
        try:
            response = self._call_ai_api(prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logging.warning(f"AI design generation failed: {e}")
        
        return None
    
    def _ai_generate_plan(self, design: DesignDocument, analysis: ProjectAnalysis, 
                         hours: int) -> Optional[Dict]:
        """Use AI to generate implementation plan"""
        if not self.api_key:
            return None
        
        prompt = f"""Generate an implementation plan for this project:
        
        Total Hours: {hours}
        Project Type: {analysis.project_type}
        Components: {', '.join([c['name'] for c in design.components[:5]])}
        
        Provide the following in JSON format:
        1. Development phases with time allocation
        2. Detailed tasks (15-20 tasks)
        3. Milestones (4-5 key milestones)
        4. Resource requirements
        
        Format as valid JSON."""
        
        try:
            response = self._call_ai_api(prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logging.warning(f"AI plan generation failed: {e}")
        
        return None
    
    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """Call AI API based on provider"""
        try:
            if self.ai_provider == 'openai':
                return self._call_openai(prompt)
            elif self.ai_provider == 'anthropic':
                return self._call_anthropic(prompt)
            elif self.ai_provider == 'gemini':
                return self._call_gemini(prompt)
        except Exception as e:
            logging.error(f"AI API call failed: {e}")
        
        return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a software architect and project planner.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        
        return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic API"""
        url = "https://api.anthropic.com/v1/messages"
        data = {
            'model': 'claude-3-haiku-20240307',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        
        return None
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
        data = {
            'contents': [{'parts': [{'text': prompt}]}]
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        
        return None
    
    def _parse_srs_response(self, data: Dict, title: str) -> SRSDocument:
        """Parse AI response into SRSDocument"""
        return SRSDocument(
            project_title=title,
            overview=data.get('overview', ''),
            scope=data.get('scope', ''),
            functional_requirements=data.get('functional_requirements', []),
            non_functional_requirements=data.get('non_functional_requirements', []),
            user_stories=data.get('user_stories', []),
            acceptance_criteria=data.get('acceptance_criteria', []),
            constraints=data.get('constraints', []),
            assumptions=data.get('assumptions', [])
        )
    
    def _parse_design_response(self, data: Dict) -> DesignDocument:
        """Parse AI response into DesignDocument"""
        return DesignDocument(
            architecture_type=data.get('architecture_type', ''),
            components=data.get('components', []),
            data_models=data.get('data_models', []),
            api_endpoints=data.get('api_endpoints', []),
            technology_stack=data.get('technology_stack', {}),
            security_considerations=data.get('security_considerations', []),
            scalability_plan=data.get('scalability_plan', '')
        )
    
    def _parse_plan_response(self, data: Dict) -> ImplementationPlan:
        """Parse AI response into ImplementationPlan"""
        return ImplementationPlan(
            phases=data.get('phases', []),
            tasks=data.get('tasks', []),
            milestones=data.get('milestones', []),
            dependencies=data.get('dependencies', []),
            timeline=data.get('timeline', {}),
            resource_allocation=data.get('resource_allocation', {})
        )
    
    def export_documents(self, srs: SRSDocument, design: DesignDocument, 
                        plan: ImplementationPlan, format: str = 'json') -> Dict[str, str]:
        """
        Export all documents in specified format
        
        Args:
            srs: SRS document
            design: Design document
            plan: Implementation plan
            format: Export format ('json', 'markdown', 'html')
            
        Returns:
            Dictionary with file paths
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"sdlc_output_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        files = {}
        
        if format == 'json':
            # Export as JSON
            files['srs'] = f"{output_dir}/srs.json"
            with open(files['srs'], 'w') as f:
                json.dump(asdict(srs), f, indent=2)
            
            files['design'] = f"{output_dir}/design.json"
            with open(files['design'], 'w') as f:
                json.dump(asdict(design), f, indent=2)
            
            files['plan'] = f"{output_dir}/implementation_plan.json"
            with open(files['plan'], 'w') as f:
                json.dump(asdict(plan), f, indent=2)
        
        elif format == 'markdown':
            # Export as Markdown
            files['srs'] = f"{output_dir}/srs.md"
            with open(files['srs'], 'w') as f:
                f.write(self._srs_to_markdown(srs))
            
            files['design'] = f"{output_dir}/design.md"
            with open(files['design'], 'w') as f:
                f.write(self._design_to_markdown(design))
            
            files['plan'] = f"{output_dir}/implementation_plan.md"
            with open(files['plan'], 'w') as f:
                f.write(self._plan_to_markdown(plan))
        
        logging.info(f"✓ Documents exported to {output_dir}")
        return files
    
    def _srs_to_markdown(self, srs: SRSDocument) -> str:
        """Convert SRS to Markdown format"""
        md = f"# Software Requirements Specification\n\n"
        md += f"## {srs.project_title}\n\n"
        md += f"### Overview\n{srs.overview}\n\n"
        md += f"### Scope\n{srs.scope}\n\n"
        
        md += "### Functional Requirements\n"
        for req in srs.functional_requirements:
            md += f"- **{req['id']}**: {req['description']}\n"
        
        md += "\n### Non-Functional Requirements\n"
        for req in srs.non_functional_requirements:
            md += f"- **{req['id']}** ({req['category']}): {req['description']}\n"
        
        md += "\n### User Stories\n"
        for story in srs.user_stories:
            md += f"- **{story['id']}**: {story['story']}\n"
        
        return md
    
    def _design_to_markdown(self, design: DesignDocument) -> str:
        """Convert Design to Markdown format"""
        md = f"# System Design Document\n\n"
        md += f"## Architecture\n{design.architecture_type}\n\n"
        
        md += "## Components\n"
        for comp in design.components:
            md += f"### {comp['name']}\n{comp['description']}\n\n"
        
        md += "## Data Models\n"
        for model in design.data_models:
            md += f"### {model['name']}\n"
            md += f"- Fields: {model['fields']}\n"
            md += f"- Relationships: {model['relationships']}\n\n"
        
        return md
    
    def _plan_to_markdown(self, plan: ImplementationPlan) -> str:
        """Convert Plan to Markdown format"""
        md = f"# Implementation Plan\n\n"
        
        md += "## Timeline\n"
        md += f"- Total Hours: {plan.timeline['total_hours']}\n"
        md += f"- Total Days: {plan.timeline['total_days']}\n"
        md += f"- Total Weeks: {plan.timeline['total_weeks']}\n\n"
        
        md += "## Phases\n"
        for phase in plan.phases:
            md += f"### {phase['name']}\n"
            md += f"- Duration: {phase['hours']} hours ({phase['days']} days)\n"
            md += f"- Description: {phase['description']}\n\n"
        
        md += "## Milestones\n"
        for milestone in plan.milestones:
            md += f"- **{milestone['name']}**: {milestone['deliverable']}\n"
        
        return md


# Example usage
if __name__ == "__main__":
    # Example project description
    project_description = """
    I need a web application for managing a small e-commerce business. 
    The system should have:
    - Product catalog with categories
    - Shopping cart functionality
    - User registration and login
    - Order management
    - Payment integration with Stripe
    - Admin dashboard for managing products and orders
    - Mobile-responsive design
    
    Technologies preferred: React for frontend, Node.js for backend, PostgreSQL for database.
    The project should be completed within 2 months.
    """
    
    # Initialize service
    sdlc_service = AutoSDLCService(ai_provider='openai')
    
    # Analyze project
    analysis = sdlc_service.analyze_project(project_description, {'minimum': 5000, 'maximum': 10000})
    print(f"\nProject Analysis:\n{json.dumps(asdict(analysis), indent=2)}")
    
    # Generate SRS
    srs = sdlc_service.generate_srs(project_description, analysis, "E-Commerce Web App")
    print(f"\nSRS Generated: {srs.project_title}")
    
    # Generate Design
    design = sdlc_service.generate_design(srs, analysis)
    print(f"\nDesign Generated: {design.architecture_type}")
    
    # Generate Implementation Plan
    plan = sdlc_service.generate_implementation_plan(design, analysis, analysis.estimated_hours)
    print(f"\nPlan Generated: {len(plan.tasks)} tasks across {len(plan.phases)} phases")
    
    # Export documents
    files = sdlc_service.export_documents(srs, design, plan, format='markdown')
    print(f"\nDocuments exported: {files}")