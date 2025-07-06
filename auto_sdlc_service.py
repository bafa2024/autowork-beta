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
class UIDesignDocument:
    """UI Design document structure for HTML interfaces"""
    design_system: Dict[str, str]  # Colors, fonts, spacing, etc.
    page_layouts: List[Dict[str, str]]  # Main pages and their layouts
    components: List[Dict[str, str]]  # Reusable UI components
    wireframes: List[Dict[str, str]]  # Wireframe descriptions
    responsive_breakpoints: List[str]  # Mobile, tablet, desktop
    accessibility_features: List[str]  # WCAG compliance features
    html_templates: List[Dict[str, str]]  # Generated HTML templates
    css_framework: str  # Bootstrap, Tailwind, custom, etc.
    javascript_libraries: List[str]  # jQuery, React, Vue, etc.
    interactive_elements: List[Dict[str, str]]  # Forms, buttons, modals, etc.
    
@dataclass
class ImplementationPlan:
    """Implementation plan with tasks breakdown"""
    phases: List[Dict[str, any]]
    tasks: List[Dict[str, any]]
    milestones: List[Dict[str, str]]
    dependencies: List[Dict[str, str]]
    timeline: Dict[str, any]
    resource_allocation: Dict[str, any]

@dataclass
class TaskBreakdown:
    """Detailed task breakdown for requirements"""
    requirement_id: str
    requirement_description: str
    tasks: List[Dict[str, any]]
    estimated_hours: int
    dependencies: List[str]
    complexity: str  # low, medium, high
    priority: str  # critical, high, medium, low

@dataclass
class ProductVersion:
    """Product version with features and tasks"""
    version: str  # e.g., "0.0.1", "0.0.2", "1.0.0"
    name: str  # e.g., "MVP", "Beta", "Release Candidate"
    description: str
    features: List[Dict[str, str]]  # Features included in this version
    tasks: List[Dict[str, any]]  # Tasks to complete this version
    estimated_hours: int
    dependencies: List[str]  # Versions this depends on
    release_criteria: List[str]  # Criteria for release
    testing_requirements: List[str]
    deployment_notes: str

@dataclass
class ImplementationTools:
    """Modern tools and resources for implementation"""
    development_tools: List[Dict[str, str]]  # IDEs, editors, etc.
    frameworks: List[Dict[str, str]]  # Frontend, backend frameworks
    databases: List[Dict[str, str]]  # Database solutions
    cloud_services: List[Dict[str, str]]  # Cloud platforms and services
    devops_tools: List[Dict[str, str]]  # CI/CD, deployment tools
    testing_tools: List[Dict[str, str]]  # Testing frameworks and tools
    monitoring_tools: List[Dict[str, str]]  # Monitoring and analytics
    security_tools: List[Dict[str, str]]  # Security and compliance tools
    collaboration_tools: List[Dict[str, str]]  # Team collaboration tools
    learning_resources: List[Dict[str, str]]  # Documentation, tutorials, courses

class AutoSDLCService:
    def __init__(self, ai_provider: Optional[str] = "openai"):
        """
        Initialize Auto SDLC Service
        
        Args:
            ai_provider: AI service provider ("openai", "anthropic", "gemini")
        """
        self.ai_provider = ai_provider or "openai"
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
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key based on provider"""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'gemini': 'GOOGLE_API_KEY'
        }
        
        provider = self.ai_provider or 'openai'
        env_var = key_mapping.get(provider)
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
            logging.warning(f"No API key found for {provider}. Set {env_var} environment variable.")
            
        return api_key
    
    def _setup_headers(self) -> Dict:
        """Setup API headers based on provider"""
        provider = self.ai_provider or 'openai'
        if provider == 'openai':
            return {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        elif provider == 'anthropic':
            return {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
        elif provider == 'gemini':
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
    
    def analyze_project(self, project_description: str, budget: Optional[Dict] = None) -> ProjectAnalysis:
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
        estimated_hours = self._estimate_hours(complexity, project_type, budget or {})
        
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
            return max(scores, key=lambda k: scores.get(k, 0))
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
    
    def _estimate_hours(self, complexity: str, project_type: str, budget: Optional[Dict] = None) -> int:
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
        logging.info("🏗️ Generating system design...")
        
        # Use AI if available
        if self.api_key:
            design_data = self._ai_generate_design(srs, analysis)
            if design_data:
                return self._parse_design_response(design_data)
        
        # Fallback to template-based generation
        return self._template_generate_design(srs, analysis)
    
    def generate_ui_design(self, design: DesignDocument, srs: SRSDocument, analysis: ProjectAnalysis) -> UIDesignDocument:
        """
        Generate UI design document with HTML templates
        
        Args:
            design: System design document
            srs: SRS document
            analysis: Project analysis
            
        Returns:
            UIDesignDocument object
        """
        logging.info("🎨 Generating UI design...")
        
        # Use AI if available
        if self.api_key:
            ui_data = self._ai_generate_ui_design(design, srs, analysis)
            if ui_data:
                return self._parse_ui_response(ui_data)
        
        # Fallback to template-based generation
        return self._template_generate_ui_design(design, srs, analysis)
    
    def _template_generate_ui_design(self, design: DesignDocument, srs: SRSDocument, analysis: ProjectAnalysis) -> UIDesignDocument:
        """Generate UI design using templates"""
        
        # Determine CSS framework based on tech stack
        css_framework = self._determine_css_framework(design.technology_stack)
        
        # Generate design system
        design_system = {
            'primary_color': '#3b82f6',
            'secondary_color': '#6b7280',
            'accent_color': '#10b981',
            'font_family': 'Inter, system-ui, sans-serif',
            'font_size_base': '16px',
            'spacing_unit': '0.25rem',
            'border_radius': '0.375rem',
            'box_shadow': '0 1px 3px rgba(0, 0, 0, 0.1)'
        }
        
        # Generate page layouts based on functional requirements
        page_layouts = self._generate_page_layouts(srs.functional_requirements)
        
        # Generate reusable components
        components = self._generate_ui_components(design.components)
        
        # Generate wireframes
        wireframes = self._generate_wireframes(page_layouts)
        
        # Generate responsive breakpoints
        responsive_breakpoints = ['320px (Mobile)', '768px (Tablet)', '1024px (Desktop)', '1440px (Large Desktop)']
        
        # Generate accessibility features
        accessibility_features = [
            'Semantic HTML structure',
            'ARIA labels and roles',
            'Keyboard navigation support',
            'High contrast mode support',
            'Screen reader compatibility'
        ]
        
        # Generate HTML templates
        html_templates = self._generate_html_templates(page_layouts, components, css_framework)
        
        # Determine JavaScript libraries
        js_libraries = self._determine_js_libraries(design.technology_stack)
        
        # Generate interactive elements
        interactive_elements = self._generate_interactive_elements(srs.functional_requirements)
        
        ui_design = UIDesignDocument(
            design_system=design_system,
            page_layouts=page_layouts,
            components=components,
            wireframes=wireframes,
            responsive_breakpoints=responsive_breakpoints,
            accessibility_features=accessibility_features,
            html_templates=html_templates,
            css_framework=css_framework,
            javascript_libraries=js_libraries,
            interactive_elements=interactive_elements
        )
        
        logging.info("✓ UI design generated")
        return ui_design
    
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
    
    def parse_requirements_to_tasks(self, srs: SRSDocument, analysis: ProjectAnalysis) -> List[TaskBreakdown]:
        """
        Parse functional requirements into detailed tasks
        
        Args:
            srs: SRS document
            analysis: Project analysis
            
        Returns:
            List of TaskBreakdown objects
        """
        logging.info("🔍 Parsing requirements into detailed tasks...")
        
        task_breakdowns = []
        
        for req in srs.functional_requirements:
            tasks = self._breakdown_requirement_to_tasks(req, analysis)
            
            breakdown = TaskBreakdown(
                requirement_id=req['id'],
                requirement_description=req['description'],
                tasks=tasks,
                estimated_hours=sum(task['estimated_hours'] for task in tasks),
                dependencies=self._identify_requirement_dependencies(req, srs.functional_requirements),
                complexity=self._assess_requirement_complexity(req, analysis),
                priority=self._assess_requirement_priority(req, srs.functional_requirements)
            )
            
            task_breakdowns.append(breakdown)
        
        logging.info(f"✓ Parsed {len(task_breakdowns)} requirements into {sum(len(bd.tasks) for bd in task_breakdowns)} tasks")
        return task_breakdowns
    
    def create_versioned_releases(self, task_breakdowns: List[TaskBreakdown], analysis: ProjectAnalysis) -> List[ProductVersion]:
        """
        Create versioned product releases from task breakdowns
        
        Args:
            task_breakdowns: List of task breakdowns
            analysis: Project analysis
            
        Returns:
            List of ProductVersion objects
        """
        logging.info("📦 Creating versioned product releases...")
        
        versions = []
        current_version = 0.0
        current_minor = 1
        
        # Group tasks by priority and complexity
        critical_tasks = []
        high_priority_tasks = []
        medium_priority_tasks = []
        low_priority_tasks = []
        
        for breakdown in task_breakdowns:
            for task in breakdown.tasks:
                task_with_requirement = {
                    **task,
                    'requirement_id': breakdown.requirement_id,
                    'requirement_description': breakdown.requirement_description,
                    'priority': breakdown.priority,
                    'complexity': breakdown.complexity
                }
                
                if breakdown.priority == 'critical':
                    critical_tasks.append(task_with_requirement)
                elif breakdown.priority == 'high':
                    high_priority_tasks.append(task_with_requirement)
                elif breakdown.priority == 'medium':
                    medium_priority_tasks.append(task_with_requirement)
                else:
                    low_priority_tasks.append(task_with_requirement)
        
        # Version 0.0.1 - MVP (Critical tasks only)
        if critical_tasks:
            mvp_tasks = critical_tasks[:min(5, len(critical_tasks))]  # Limit to 5 tasks for MVP
            mvp_version = self._create_version(
                version="0.0.1",
                name="MVP (Minimum Viable Product)",
                description="Core functionality to demonstrate basic project value",
                tasks=mvp_tasks,
                dependencies=[],
                analysis=analysis
            )
            versions.append(mvp_version)
            current_minor = 2
        
        # Version 0.0.2 - Enhanced MVP (Remaining critical + some high priority)
        remaining_critical = critical_tasks[5:] if len(critical_tasks) > 5 else []
        enhanced_tasks = remaining_critical + high_priority_tasks[:3]
        
        if enhanced_tasks:
            enhanced_version = self._create_version(
                version=f"0.0.{current_minor}",
                name="Enhanced MVP",
                description="Additional critical features and high-priority functionality",
                tasks=enhanced_tasks,
                dependencies=["0.0.1"] if versions else [],
                analysis=analysis
            )
            versions.append(enhanced_version)
            current_minor += 1
        
        # Version 0.0.3+ - Feature Releases (High and medium priority)
        remaining_high = high_priority_tasks[3:] if len(high_priority_tasks) > 3 else []
        feature_tasks = remaining_high + medium_priority_tasks[:4]
        
        if feature_tasks:
            feature_version = self._create_version(
                version=f"0.0.{current_minor}",
                name="Feature Release",
                description="Additional features and improvements",
                tasks=feature_tasks,
                dependencies=[v.version for v in versions[-2:]] if len(versions) >= 2 else [v.version for v in versions],
                analysis=analysis
            )
            versions.append(feature_version)
            current_minor += 1
        
        # Version 0.1.0 - Beta Release (Remaining medium + some low priority)
        remaining_medium = medium_priority_tasks[4:] if len(medium_priority_tasks) > 4 else []
        beta_tasks = remaining_medium + low_priority_tasks[:3]
        
        if beta_tasks:
            beta_version = self._create_version(
                version="0.1.0",
                name="Beta Release",
                description="Feature-complete version ready for beta testing",
                tasks=beta_tasks,
                dependencies=[v.version for v in versions[-2:]] if len(versions) >= 2 else [v.version for v in versions],
                analysis=analysis
            )
            versions.append(beta_version)
        
        # Version 0.2.0 - Release Candidate (Remaining low priority + polish)
        remaining_low = low_priority_tasks[3:] if len(low_priority_tasks) > 3 else []
        polish_tasks = remaining_low + self._generate_polish_tasks(analysis)
        
        if polish_tasks:
            rc_version = self._create_version(
                version="0.2.0",
                name="Release Candidate",
                description="Final polish and optimization before production release",
                tasks=polish_tasks,
                dependencies=["0.1.0"] if any(v.version == "0.1.0" for v in versions) else [v.version for v in versions[-2:]],
                analysis=analysis
            )
            versions.append(rc_version)
        
        # Version 1.0.0 - Production Release
        production_version = self._create_version(
            version="1.0.0",
            name="Production Release",
            description="Final production-ready version with all features and optimizations",
            tasks=self._generate_production_tasks(analysis),
            dependencies=[v.version for v in versions[-2:]] if len(versions) >= 2 else [v.version for v in versions],
            analysis=analysis
        )
        versions.append(production_version)
        
        logging.info(f"✓ Created {len(versions)} versioned releases")
        return versions
    
    def _breakdown_requirement_to_tasks(self, requirement: Dict[str, str], analysis: ProjectAnalysis) -> List[Dict[str, any]]:
        """Break down a single requirement into detailed tasks"""
        tasks = []
        req_text = requirement['description'].lower()
        req_id = requirement['id']
        
        # Database tasks
        if any(word in req_text for word in ['store', 'save', 'database', 'data', 'record']):
            tasks.extend([
                {
                    'id': f'{req_id}_DB_01',
                    'title': f'Create database schema for {requirement["id"]}',
                    'description': f'Design and implement database tables/collections for {requirement["description"]}',
                    'type': 'database',
                    'estimated_hours': 2,
                    'complexity': 'medium'
                },
                {
                    'id': f'{req_id}_DB_02',
                    'title': f'Implement data access layer for {requirement["id"]}',
                    'description': f'Create repository/service layer for {requirement["description"]}',
                    'type': 'backend',
                    'estimated_hours': 3,
                    'complexity': 'medium'
                }
            ])
        
        # API tasks
        if any(word in req_text for word in ['api', 'endpoint', 'service', 'backend']):
            tasks.extend([
                {
                    'id': f'{req_id}_API_01',
                    'title': f'Create API endpoints for {requirement["id"]}',
                    'description': f'Implement REST/GraphQL endpoints for {requirement["description"]}',
                    'type': 'backend',
                    'estimated_hours': 4,
                    'complexity': 'medium'
                },
                {
                    'id': f'{req_id}_API_02',
                    'title': f'Add API validation for {requirement["id"]}',
                    'description': f'Implement input validation and error handling for {requirement["description"]}',
                    'type': 'backend',
                    'estimated_hours': 2,
                    'complexity': 'low'
                }
            ])
        
        # Frontend tasks
        if any(word in req_text for word in ['ui', 'interface', 'form', 'page', 'view', 'display']):
            tasks.extend([
                {
                    'id': f'{req_id}_UI_01',
                    'title': f'Create UI components for {requirement["id"]}',
                    'description': f'Design and implement user interface for {requirement["description"]}',
                    'type': 'frontend',
                    'estimated_hours': 6,
                    'complexity': 'medium'
                },
                {
                    'id': f'{req_id}_UI_02',
                    'title': f'Add form validation for {requirement["id"]}',
                    'description': f'Implement client-side validation for {requirement["description"]}',
                    'type': 'frontend',
                    'estimated_hours': 2,
                    'complexity': 'low'
                },
                {
                    'id': f'{req_id}_UI_03',
                    'title': f'Add responsive design for {requirement["id"]}',
                    'description': f'Ensure mobile-friendly design for {requirement["description"]}',
                    'type': 'frontend',
                    'estimated_hours': 3,
                    'complexity': 'medium'
                }
            ])
        
        # Authentication tasks
        if any(word in req_text for word in ['login', 'register', 'auth', 'user', 'permission']):
            tasks.extend([
                {
                    'id': f'{req_id}_AUTH_01',
                    'title': f'Implement authentication for {requirement["id"]}',
                    'description': f'Add user authentication and authorization for {requirement["description"]}',
                    'type': 'security',
                    'estimated_hours': 8,
                    'complexity': 'high'
                },
                {
                    'id': f'{req_id}_AUTH_02',
                    'title': f'Add role-based access control for {requirement["id"]}',
                    'description': f'Implement user roles and permissions for {requirement["description"]}',
                    'type': 'security',
                    'estimated_hours': 4,
                    'complexity': 'medium'
                }
            ])
        
        # Integration tasks
        if any(word in req_text for word in ['integration', 'connect', 'sync', 'import', 'export']):
            tasks.extend([
                {
                    'id': f'{req_id}_INT_01',
                    'title': f'Implement integration for {requirement["id"]}',
                    'description': f'Add external service integration for {requirement["description"]}',
                    'type': 'integration',
                    'estimated_hours': 6,
                    'complexity': 'high'
                },
                {
                    'id': f'{req_id}_INT_02',
                    'title': f'Add error handling for {requirement["id"]} integration',
                    'description': f'Implement robust error handling for {requirement["description"]}',
                    'type': 'integration',
                    'estimated_hours': 3,
                    'complexity': 'medium'
                }
            ])
        
        # Testing tasks (always included)
        tasks.extend([
            {
                'id': f'{req_id}_TEST_01',
                'title': f'Write unit tests for {requirement["id"]}',
                'description': f'Create comprehensive unit tests for {requirement["description"]}',
                'type': 'testing',
                'estimated_hours': 3,
                'complexity': 'medium'
            },
            {
                'id': f'{req_id}_TEST_02',
                'title': f'Write integration tests for {requirement["id"]}',
                'description': f'Create integration tests for {requirement["description"]}',
                'type': 'testing',
                'estimated_hours': 2,
                'complexity': 'medium'
            }
        ])
        
        # Documentation tasks
        tasks.append({
            'id': f'{req_id}_DOC_01',
            'title': f'Document {requirement["id"]}',
            'description': f'Create documentation for {requirement["description"]}',
            'type': 'documentation',
            'estimated_hours': 1,
            'complexity': 'low'
        })
        
        return tasks
    
    def _identify_requirement_dependencies(self, requirement: Dict[str, str], all_requirements: List[Dict[str, str]]) -> List[str]:
        """Identify dependencies between requirements"""
        dependencies = []
        req_text = requirement['description'].lower()
        
        for other_req in all_requirements:
            if other_req['id'] != requirement['id']:
                other_text = other_req['description'].lower()
                
                # Check for common dependency patterns
                if any(word in req_text for word in ['user', 'login', 'auth']) and any(word in other_text for word in ['user', 'login', 'auth']):
                    if other_req['id'] not in dependencies:
                        dependencies.append(other_req['id'])
                
                if any(word in req_text for word in ['database', 'data']) and any(word in other_text for word in ['database', 'data']):
                    if other_req['id'] not in dependencies:
                        dependencies.append(other_req['id'])
        
        return dependencies
    
    def _assess_requirement_complexity(self, requirement: Dict[str, str], analysis: ProjectAnalysis) -> str:
        """Assess the complexity of a requirement"""
        req_text = requirement['description'].lower()
        
        # Count complexity indicators
        complexity_indicators = 0
        
        if any(word in req_text for word in ['integration', 'api', 'external']):
            complexity_indicators += 2
        
        if any(word in req_text for word in ['authentication', 'security', 'permission']):
            complexity_indicators += 2
        
        if any(word in req_text for word in ['real-time', 'websocket', 'notification']):
            complexity_indicators += 2
        
        if any(word in req_text for word in ['report', 'analytics', 'dashboard']):
            complexity_indicators += 1
        
        if any(word in req_text for word in ['upload', 'file', 'image']):
            complexity_indicators += 1
        
        if complexity_indicators >= 4:
            return 'high'
        elif complexity_indicators >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _assess_requirement_priority(self, requirement: Dict[str, str], all_requirements: List[Dict[str, str]]) -> str:
        """Assess the priority of a requirement"""
        req_text = requirement['description'].lower()
        
        # Critical indicators
        if any(word in req_text for word in ['core', 'essential', 'must', 'critical', 'basic']):
            return 'critical'
        
        # High priority indicators
        if any(word in req_text for word in ['important', 'key', 'main', 'primary']):
            return 'high'
        
        # Low priority indicators
        if any(word in req_text for word in ['nice', 'optional', 'bonus', 'extra']):
            return 'low'
        
        # Default to medium
        return 'medium'
    
    def _create_version(self, version: str, name: str, description: str, tasks: List[Dict], dependencies: List[str], analysis: ProjectAnalysis) -> ProductVersion:
        """Create a product version with the given parameters"""
        
        # Extract features from tasks
        features = []
        for task in tasks:
            if task['type'] in ['frontend', 'backend', 'database']:
                features.append({
                    'id': task['id'],
                    'name': task['title'],
                    'description': task['description'],
                    'type': task['type']
                })
        
        # Generate release criteria
        release_criteria = [
            f"All {len(tasks)} tasks completed",
            "Unit tests passing",
            "Integration tests passing",
            "Code review completed",
            "Documentation updated"
        ]
        
        # Generate testing requirements
        testing_requirements = [
            "Unit test coverage > 80%",
            "Integration tests for all features",
            "Manual testing on multiple browsers",
            "Mobile responsiveness testing",
            "Performance testing"
        ]
        
        # Generate deployment notes
        deployment_notes = f"""
        Version {version} - {name}
        
        Features included:
        {chr(10).join([f"- {feature['name']}" for feature in features[:5]])}
        
        Dependencies: {', '.join(dependencies) if dependencies else 'None'}
        
        Estimated deployment time: {sum(task['estimated_hours'] for task in tasks) // 8} days
        """
        
        return ProductVersion(
            version=version,
            name=name,
            description=description,
            features=features,
            tasks=tasks,
            estimated_hours=sum(task['estimated_hours'] for task in tasks),
            dependencies=dependencies,
            release_criteria=release_criteria,
            testing_requirements=testing_requirements,
            deployment_notes=deployment_notes.strip()
        )
    
    def _generate_polish_tasks(self, analysis: ProjectAnalysis) -> List[Dict[str, any]]:
        """Generate polish tasks for release candidate"""
        return [
            {
                'id': 'POLISH_01',
                'title': 'Performance optimization',
                'description': 'Optimize application performance and loading times',
                'type': 'optimization',
                'estimated_hours': 4,
                'complexity': 'medium'
            },
            {
                'id': 'POLISH_02',
                'title': 'UI/UX improvements',
                'description': 'Polish user interface and improve user experience',
                'type': 'frontend',
                'estimated_hours': 6,
                'complexity': 'medium'
            },
            {
                'id': 'POLISH_03',
                'title': 'Security audit',
                'description': 'Conduct security audit and fix vulnerabilities',
                'type': 'security',
                'estimated_hours': 8,
                'complexity': 'high'
            },
            {
                'id': 'POLISH_04',
                'title': 'Documentation review',
                'description': 'Review and update all documentation',
                'type': 'documentation',
                'estimated_hours': 3,
                'complexity': 'low'
            }
        ]
    
    def _generate_production_tasks(self, analysis: ProjectAnalysis) -> List[Dict[str, any]]:
        """Generate production release tasks"""
        return [
            {
                'id': 'PROD_01',
                'title': 'Production deployment setup',
                'description': 'Configure production environment and deployment pipeline',
                'type': 'deployment',
                'estimated_hours': 6,
                'complexity': 'high'
            },
            {
                'id': 'PROD_02',
                'title': 'Monitoring and logging setup',
                'description': 'Implement application monitoring and logging',
                'type': 'infrastructure',
                'estimated_hours': 4,
                'complexity': 'medium'
            },
            {
                'id': 'PROD_03',
                'title': 'Backup and recovery setup',
                'description': 'Configure backup and disaster recovery procedures',
                'type': 'infrastructure',
                'estimated_hours': 3,
                'complexity': 'medium'
            },
            {
                'id': 'PROD_04',
                'title': 'Final testing and validation',
                'description': 'Conduct final testing in production environment',
                'type': 'testing',
                'estimated_hours': 4,
                'complexity': 'medium'
            }
        ]
    
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
    
    def _ai_generate_ui_design(self, design: DesignDocument, srs: SRSDocument, analysis: ProjectAnalysis) -> Optional[Dict]:
        """Use AI to generate UI design document"""
        if not self.api_key:
            return None
        
        prompt = f"""Generate a UI design document for this project:
        
        Project Type: {analysis.project_type}
        System Design Summary: {design.architecture_type}
        Functional Requirements: {', '.join([req['description'] for req in srs.functional_requirements[:5]])}
        
        Provide the following in JSON format:
        1. Design System (colors, fonts, spacing, etc.)
        2. Page Layouts (main pages and their layouts)
        3. Reusable Components (list of 5-8 components with descriptions)
        4. Wireframes (descriptions of wireframe layouts)
        5. Responsive Breakpoints (mobile, tablet, desktop, large desktop)
        6. Accessibility Features (WCAG compliance)
        7. HTML Templates (generated HTML for pages)
        8. CSS Framework (Bootstrap, Tailwind, etc.)
        9. JavaScript Libraries (jQuery, React, Vue, etc.)
        10. Interactive Elements (forms, buttons, modals, etc.)
        
        Format as valid JSON."""
        
        try:
            response = self._call_ai_api(prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logging.warning(f"AI UI design generation failed: {e}")
        
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
    
    def _parse_ui_response(self, data: Dict) -> UIDesignDocument:
        """Parse AI response into UIDesignDocument"""
        return UIDesignDocument(
            design_system=data.get('design_system', {}),
            page_layouts=data.get('page_layouts', []),
            components=data.get('components', []),
            wireframes=data.get('wireframes', []),
            responsive_breakpoints=data.get('responsive_breakpoints', []),
            accessibility_features=data.get('accessibility_features', []),
            html_templates=data.get('html_templates', []),
            css_framework=data.get('css_framework', ''),
            javascript_libraries=data.get('javascript_libraries', []),
            interactive_elements=data.get('interactive_elements', [])
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
    
    def _determine_css_framework(self, tech_stack: Dict[str, List[str]]) -> str:
        """Determine CSS framework based on technology stack"""
        frontend_techs = tech_stack.get('frontend', [])
        
        if 'Tailwind' in str(frontend_techs):
            return 'Tailwind CSS'
        elif 'Bootstrap' in str(frontend_techs):
            return 'Bootstrap'
        elif 'Material-UI' in str(frontend_techs) or 'MUI' in str(frontend_techs):
            return 'Material-UI'
        elif 'Ant Design' in str(frontend_techs):
            return 'Ant Design'
        else:
            return 'Custom CSS'
    
    def _generate_page_layouts(self, functional_reqs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate page layouts based on functional requirements"""
        layouts = []
        
        # Common pages based on requirements
        common_pages = {
            'authentication': ['login', 'register', 'forgot-password'],
            'dashboard': ['dashboard', 'overview', 'analytics'],
            'data_management': ['list', 'create', 'edit', 'view', 'delete'],
            'settings': ['profile', 'preferences', 'admin']
        }
        
        for req in functional_reqs:
            req_text = req['description'].lower()
            
            if any(word in req_text for word in ['login', 'register', 'auth']):
                for page in common_pages['authentication']:
                    layouts.append({
                        'name': f'{page.title()} Page',
                        'type': 'authentication',
                        'description': f'{page.title()} page with form validation',
                        'layout': 'centered-form'
                    })
            
            elif any(word in req_text for word in ['dashboard', 'overview', 'analytics']):
                for page in common_pages['dashboard']:
                    layouts.append({
                        'name': f'{page.title()} Page',
                        'type': 'dashboard',
                        'description': f'{page.title()} page with data visualization',
                        'layout': 'sidebar-main'
                    })
            
            elif any(word in req_text for word in ['create', 'edit', 'view', 'list', 'manage']):
                for page in common_pages['data_management']:
                    layouts.append({
                        'name': f'{page.title()} Page',
                        'type': 'data_management',
                        'description': f'{page.title()} page with CRUD operations',
                        'layout': 'header-content'
                    })
        
        # Add default pages if none generated
        if not layouts:
            layouts = [
                {
                    'name': 'Home Page',
                    'type': 'landing',
                    'description': 'Main landing page',
                    'layout': 'hero-content'
                },
                {
                    'name': 'Dashboard Page',
                    'type': 'dashboard',
                    'description': 'Main dashboard page',
                    'layout': 'sidebar-main'
                }
            ]
        
        return layouts
    
    def _generate_ui_components(self, system_components: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate reusable UI components"""
        components = []
        
        # Common UI components
        common_components = [
            {
                'name': 'Navigation Bar',
                'type': 'navigation',
                'description': 'Main navigation component with responsive menu',
                'html_template': '<nav class="navbar">...</nav>'
            },
            {
                'name': 'Card Component',
                'type': 'content',
                'description': 'Reusable card component for content display',
                'html_template': '<div class="card">...</div>'
            },
            {
                'name': 'Button Component',
                'type': 'interaction',
                'description': 'Standard button component with variants',
                'html_template': '<button class="btn btn-primary">...</button>'
            },
            {
                'name': 'Form Component',
                'type': 'input',
                'description': 'Form component with validation',
                'html_template': '<form class="form">...</form>'
            },
            {
                'name': 'Modal Component',
                'type': 'overlay',
                'description': 'Modal dialog component',
                'html_template': '<div class="modal">...</div>'
            }
        ]
        
        # Add system-specific components
        for comp in system_components:
            components.append({
                'name': f'{comp["name"]} Component',
                'type': 'system',
                'description': f'UI component for {comp["name"].lower()}',
                'html_template': f'<div class="{comp["name"].lower().replace(" ", "-")}-component">...</div>'
            })
        
        components.extend(common_components)
        return components
    
    def _generate_wireframes(self, page_layouts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate wireframe descriptions"""
        wireframes = []
        
        for layout in page_layouts:
            wireframes.append({
                'page': layout['name'],
                'description': f'Wireframe for {layout["name"]} with {layout["layout"]} layout',
                'sections': ['Header', 'Navigation', 'Main Content', 'Sidebar', 'Footer'],
                'layout_type': layout['layout']
            })
        
        return wireframes
    
    def _generate_html_templates(self, page_layouts: List[Dict[str, str]], components: List[Dict[str, str]], css_framework: str) -> List[Dict[str, str]]:
        """Generate ready-to-use prompts for LLMs to create HTML templates"""
        prompts = []
        for layout in page_layouts:
            prompt = (
                f"Generate a responsive HTML page for '{layout['name']}'.\n"
                f"Page type: {layout['type']}.\n"
                f"Description: {layout['description']}.\n"
                f"Use CSS framework: {css_framework}.\n"
                f"Include the following UI components: "
                + ', '.join([c['name'] for c in components if c.get('page') == layout['name'] or c.get('page', '').lower() in layout['name'].lower()])
                + ".\nMake it mobile-friendly and accessible."
            )
            prompts.append({
                'page': layout['name'],
                'css_framework': css_framework,
                'prompt': prompt
            })
        return prompts
    
    def _determine_js_libraries(self, tech_stack: Dict[str, List[str]]) -> List[str]:
        """Determine JavaScript libraries based on technology stack"""
        frontend_techs = tech_stack.get('frontend', [])
        js_libs = []
        
        if 'React' in str(frontend_techs):
            js_libs.extend(['React', 'React DOM'])
        elif 'Vue' in str(frontend_techs):
            js_libs.extend(['Vue.js'])
        elif 'Angular' in str(frontend_techs):
            js_libs.extend(['Angular'])
        else:
            js_libs.append('Vanilla JavaScript')
        
        # Add utility libraries
        js_libs.extend(['jQuery', 'Axios'])
        
        return js_libs
    
    def _generate_interactive_elements(self, functional_reqs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Generate interactive elements based on functional requirements"""
        elements = []
        
        for req in functional_reqs:
            req_text = req['description'].lower()
            
            if any(word in req_text for word in ['form', 'input', 'submit']):
                elements.append({
                    'name': 'Form Submission',
                    'type': 'form',
                    'description': 'Form validation and submission handling',
                    'javascript': 'handleFormSubmit()'
                })
            
            elif any(word in req_text for word in ['button', 'click', 'action']):
                elements.append({
                    'name': 'Button Actions',
                    'type': 'button',
                    'description': 'Button click handlers and actions',
                    'javascript': 'handleButtonClick()'
                })
            
            elif any(word in req_text for word in ['modal', 'popup', 'dialog']):
                elements.append({
                    'name': 'Modal Dialogs',
                    'type': 'modal',
                    'description': 'Modal popup functionality',
                    'javascript': 'showModal()'
                })
            
            elif any(word in req_text for word in ['table', 'list', 'grid']):
                elements.append({
                    'name': 'Data Tables',
                    'type': 'table',
                    'description': 'Sortable and filterable data tables',
                    'javascript': 'initializeDataTable()'
                })
        
        # Add default interactive elements
        if not elements:
            elements = [
                {
                    'name': 'Navigation Menu',
                    'type': 'navigation',
                    'description': 'Responsive navigation menu',
                    'javascript': 'toggleMenu()'
                },
                {
                    'name': 'Form Validation',
                    'type': 'form',
                    'description': 'Client-side form validation',
                    'javascript': 'validateForm()'
                }
            ]
        
        return elements
    
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

    def generate_complete_sdlc(self, project_description: str) -> Dict[str, any]:
        """
        Generate complete SDLC documents including task breakdown and versioned releases
        
        Args:
            project_description: Project description
            
        Returns:
            Dictionary containing all SDLC documents
        """
        logging.info("🚀 Starting complete SDLC generation...")
        
        try:
            # Step 1: Project Analysis
            analysis = self.analyze_project(project_description)
            logging.info("✓ Project analysis completed")
            
            # Step 2: SRS Document
            srs = self.generate_srs(project_description, analysis, "Project")
            logging.info("✓ SRS document generated")
            
            # Step 3: System Design Document
            design = self.generate_design(srs, analysis)
            logging.info("✓ System design document generated")
            
            # Step 4: UI Design Document
            ui_design = self.generate_ui_design(design, srs, analysis)
            logging.info("✓ UI design document generated")
            
            # Step 5: Implementation Plan
            estimated_hours = self._estimate_project_hours(analysis)
            implementation_plan = self.generate_implementation_plan(design, analysis, estimated_hours)
            logging.info("✓ Implementation plan generated")
            
            # Step 6: Implementation Tools and Resources
            implementation_tools = self.generate_implementation_tools(analysis, design)
            logging.info("✓ Implementation tools generated")
            
            # Step 7: Task Breakdown and Versioned Releases
            task_breakdowns = self.parse_requirements_to_tasks(srs, analysis)
            logging.info("✓ Task breakdown completed")
            
            versioned_releases = self.create_versioned_releases(task_breakdowns, analysis)
            logging.info("✓ Versioned releases created")
            
            # Step 8: Test Plan
            test_plan = self.generate_test_plan(analysis, srs, design)
            logging.info("✓ Test plan generated")
            
            # Step 9: Deployment Plan
            deployment_plan = self.generate_deployment_plan(analysis, design)
            logging.info("✓ Deployment plan generated")
            
            # Step 10: Maintenance Plan
            maintenance_plan = self.generate_maintenance_plan(analysis, design)
            logging.info("✓ Maintenance plan generated")
            
            # Coding and Testing Prompts
            coding_prompts = self._generate_coding_prompts(design, ui_design)
            testing_prompts = self._generate_testing_prompts(design, ui_design, implementation_plan)
            
            # Compile all documents
            result = {
                'project_analysis': analysis.__dict__,
                'srs_document': srs.__dict__,
                'system_design': design.__dict__,
                'ui_design': ui_design.__dict__,
                'implementation_plan': implementation_plan.__dict__,
                'implementation_tools': implementation_tools.__dict__,
                'task_breakdowns': [bd.__dict__ for bd in task_breakdowns],
                'versioned_releases': [vr.__dict__ for vr in versioned_releases],
                'test_plan': test_plan,
                'deployment_plan': deployment_plan,
                'maintenance_plan': maintenance_plan,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_estimated_hours': estimated_hours,
                    'project_complexity': analysis.complexity,
                    'recommended_team_size': self._calculate_recommended_team_size(analysis),
                    'total_tasks': sum(len(bd.tasks) for bd in task_breakdowns),
                    'total_versions': len(versioned_releases)
                },
                'coding_prompts': coding_prompts,
                'testing_prompts': testing_prompts
            }
            
            logging.info("🎉 Complete SDLC generation completed successfully!")
            return result
            
        except Exception as e:
            logging.error(f"❌ Error during complete SDLC generation: {str(e)}")
            raise

    def _estimate_project_hours(self, analysis: ProjectAnalysis) -> int:
        """Estimate total project hours"""
        return analysis.estimated_hours

    def _calculate_recommended_team_size(self, analysis: ProjectAnalysis) -> int:
        """Calculate recommended team size based on project complexity and hours"""
        # Base team size on complexity
        complexity_team_size = {
            'low': 1,
            'medium': 2,
            'high': 3
        }
        
        base_size = complexity_team_size.get(analysis.complexity, 2)
        
        # Adjust based on project hours
        if analysis.estimated_hours > 200:
            base_size += 1
        elif analysis.estimated_hours > 400:
            base_size += 2
        
        # Adjust based on project type
        if analysis.project_type in ['mobile_app', 'web_app']:
            base_size += 1  # Need frontend and backend developers
        
        return min(base_size, 5)  # Cap at 5 team members

    def generate_test_plan(self, analysis: ProjectAnalysis, srs: SRSDocument, design: DesignDocument) -> Dict[str, any]:
        """Generate test plan"""
        return {
            'test_strategy': 'Comprehensive testing approach including unit, integration, and user acceptance testing',
            'test_phases': [
                {'phase': 'Unit Testing', 'description': 'Test individual components'},
                {'phase': 'Integration Testing', 'description': 'Test component interactions'},
                {'phase': 'System Testing', 'description': 'Test complete system'},
                {'phase': 'User Acceptance Testing', 'description': 'Validate with end users'}
            ],
            'test_cases': [],
            'test_environment': 'Development, staging, and production environments',
            'automation_plan': 'Automate unit and integration tests'
        }

    def generate_deployment_plan(self, analysis: ProjectAnalysis, design: DesignDocument) -> Dict[str, any]:
        """Generate deployment plan"""
        return {
            'deployment_strategy': 'Blue-green deployment for zero downtime',
            'environments': ['Development', 'Staging', 'Production'],
            'deployment_steps': [
                'Code review and approval',
                'Automated testing',
                'Staging deployment',
                'User acceptance testing',
                'Production deployment',
                'Post-deployment monitoring'
            ],
            'rollback_plan': 'Quick rollback to previous version if issues arise',
            'monitoring': 'Application performance monitoring and alerting'
        }

    def generate_maintenance_plan(self, analysis: ProjectAnalysis, design: DesignDocument) -> Dict[str, any]:
        """Generate maintenance plan"""
        return {
            'maintenance_schedule': 'Regular maintenance windows',
            'monitoring': '24/7 system monitoring',
            'backup_strategy': 'Daily automated backups',
            'security_updates': 'Regular security patches and updates',
            'performance_optimization': 'Continuous performance monitoring and optimization',
            'support_plan': 'Technical support and bug fixes'
        }

    def generate_implementation_tools(self, analysis: ProjectAnalysis, design: DesignDocument) -> ImplementationTools:
        """Generate modern tools and resources for implementation"""
        logging.info("🛠️ Generating implementation tools and resources...")
        
        # Development tools based on project type
        dev_tools = self._get_development_tools(analysis.project_type, analysis.technologies)
        
        # Frameworks based on detected technologies
        frameworks = self._get_frameworks(analysis.technologies, analysis.project_type)
        
        # Database recommendations
        databases = self._get_database_recommendations(analysis.project_type, analysis.complexity)
        
        # Cloud services
        cloud_services = self._get_cloud_services(analysis.project_type, analysis.complexity)
        
        # DevOps tools
        devops_tools = self._get_devops_tools(analysis.complexity)
        
        # Testing tools
        testing_tools = self._get_testing_tools(analysis.technologies, analysis.project_type)
        
        # Monitoring tools
        monitoring_tools = self._get_monitoring_tools(analysis.complexity)
        
        # Security tools
        security_tools = self._get_security_tools(analysis.project_type)
        
        # Collaboration tools
        collaboration_tools = self._get_collaboration_tools(analysis.complexity)
        
        # Learning resources
        learning_resources = self._get_learning_resources(analysis.technologies, analysis.project_type)
        
        tools = ImplementationTools(
            development_tools=dev_tools,
            frameworks=frameworks,
            databases=databases,
            cloud_services=cloud_services,
            devops_tools=devops_tools,
            testing_tools=testing_tools,
            monitoring_tools=monitoring_tools,
            security_tools=security_tools,
            collaboration_tools=collaboration_tools,
            learning_resources=learning_resources
        )
        
        logging.info("✓ Implementation tools generated")
        return tools

    def _get_development_tools(self, project_type: str, technologies: List[str]) -> List[Dict[str, str]]:
        """Get development tools based on project type and technologies"""
        tools = []
        
        # Universal tools
        tools.extend([
            {'name': 'Git', 'description': 'Version control system', 'url': 'https://git-scm.com/'},
            {'name': 'GitHub', 'description': 'Code hosting and collaboration', 'url': 'https://github.com/'},
            {'name': 'VS Code', 'description': 'Lightweight code editor', 'url': 'https://code.visualstudio.com/'}
        ])
        
        # Language-specific tools
        if 'python' in technologies:
            tools.extend([
                {'name': 'PyCharm', 'description': 'Python IDE', 'url': 'https://www.jetbrains.com/pycharm/'},
                {'name': 'Jupyter Notebook', 'description': 'Interactive development', 'url': 'https://jupyter.org/'}
            ])
        
        if 'javascript' in technologies:
            tools.extend([
                {'name': 'WebStorm', 'description': 'JavaScript IDE', 'url': 'https://www.jetbrains.com/webstorm/'},
                {'name': 'Node.js', 'description': 'JavaScript runtime', 'url': 'https://nodejs.org/'}
            ])
        
        if 'java' in technologies:
            tools.extend([
                {'name': 'IntelliJ IDEA', 'description': 'Java IDE', 'url': 'https://www.jetbrains.com/idea/'},
                {'name': 'Eclipse', 'description': 'Java development platform', 'url': 'https://www.eclipse.org/'}
            ])
        
        return tools

    def _get_frameworks(self, technologies: List[str], project_type: str) -> List[Dict[str, str]]:
        """Get framework recommendations"""
        frameworks = []
        
        # Frontend frameworks
        if 'javascript' in technologies or project_type in ['web_app', 'mobile_app']:
            frameworks.extend([
                {'name': 'React', 'description': 'Frontend library', 'url': 'https://reactjs.org/'},
                {'name': 'Vue.js', 'description': 'Progressive framework', 'url': 'https://vuejs.org/'},
                {'name': 'Angular', 'description': 'Full-featured framework', 'url': 'https://angular.io/'}
            ])
        
        # Backend frameworks
        if 'python' in technologies:
            frameworks.extend([
                {'name': 'Django', 'description': 'Full-stack framework', 'url': 'https://www.djangoproject.com/'},
                {'name': 'Flask', 'description': 'Lightweight framework', 'url': 'https://flask.palletsprojects.com/'},
                {'name': 'FastAPI', 'description': 'Modern API framework', 'url': 'https://fastapi.tiangolo.com/'}
            ])
        
        if 'javascript' in technologies:
            frameworks.extend([
                {'name': 'Express.js', 'description': 'Node.js framework', 'url': 'https://expressjs.com/'},
                {'name': 'Next.js', 'description': 'React framework', 'url': 'https://nextjs.org/'},
                {'name': 'NestJS', 'description': 'Scalable framework', 'url': 'https://nestjs.com/'}
            ])
        
        return frameworks

    def _get_database_recommendations(self, project_type: str, complexity: str) -> List[Dict[str, str]]:
        """Get database recommendations"""
        databases = []
        
        # Relational databases
        databases.extend([
            {'name': 'PostgreSQL', 'description': 'Advanced open source database', 'url': 'https://www.postgresql.org/'},
            {'name': 'MySQL', 'description': 'Popular open source database', 'url': 'https://www.mysql.com/'}
        ])
        
        # NoSQL databases
        if complexity == 'high' or project_type in ['data_science', 'iot']:
            databases.extend([
                {'name': 'MongoDB', 'description': 'Document database', 'url': 'https://www.mongodb.com/'},
                {'name': 'Redis', 'description': 'In-memory data store', 'url': 'https://redis.io/'}
            ])
        
        return databases

    def _get_cloud_services(self, project_type: str, complexity: str) -> List[Dict[str, str]]:
        """Get cloud service recommendations"""
        services = []
        
        # Major cloud providers
        services.extend([
            {'name': 'AWS', 'description': 'Amazon Web Services', 'url': 'https://aws.amazon.com/'},
            {'name': 'Google Cloud', 'description': 'Google Cloud Platform', 'url': 'https://cloud.google.com/'},
            {'name': 'Azure', 'description': 'Microsoft Azure', 'url': 'https://azure.microsoft.com/'}
        ])
        
        # Specialized services
        if project_type == 'web_app':
            services.extend([
                {'name': 'Vercel', 'description': 'Frontend deployment', 'url': 'https://vercel.com/'},
                {'name': 'Netlify', 'description': 'Static site hosting', 'url': 'https://www.netlify.com/'}
            ])
        
        return services

    def _get_devops_tools(self, complexity: str) -> List[Dict[str, str]]:
        """Get DevOps tools"""
        tools = [
            {'name': 'Docker', 'description': 'Containerization', 'url': 'https://www.docker.com/'},
            {'name': 'GitHub Actions', 'description': 'CI/CD pipeline', 'url': 'https://github.com/features/actions'},
            {'name': 'Jenkins', 'description': 'Automation server', 'url': 'https://jenkins.io/'}
        ]
        
        if complexity == 'high':
            tools.extend([
                {'name': 'Kubernetes', 'description': 'Container orchestration', 'url': 'https://kubernetes.io/'},
                {'name': 'Terraform', 'description': 'Infrastructure as code', 'url': 'https://www.terraform.io/'}
            ])
        
        return tools

    def _get_testing_tools(self, technologies: List[str], project_type: str) -> List[Dict[str, str]]:
        """Get testing tools"""
        tools = []
        
        # General testing
        tools.extend([
            {'name': 'Jest', 'description': 'JavaScript testing framework', 'url': 'https://jestjs.io/'},
            {'name': 'Postman', 'description': 'API testing', 'url': 'https://www.postman.com/'}
        ])
        
        # Language-specific testing
        if 'python' in technologies:
            tools.extend([
                {'name': 'pytest', 'description': 'Python testing framework', 'url': 'https://pytest.org/'},
                {'name': 'Selenium', 'description': 'Web automation', 'url': 'https://selenium.dev/'}
            ])
        
        return tools

    def _get_monitoring_tools(self, complexity: str) -> List[Dict[str, str]]:
        """Get monitoring tools"""
        tools = [
            {'name': 'Google Analytics', 'description': 'Web analytics', 'url': 'https://analytics.google.com/'},
            {'name': 'Sentry', 'description': 'Error tracking', 'url': 'https://sentry.io/'}
        ]
        
        if complexity == 'high':
            tools.extend([
                {'name': 'Datadog', 'description': 'Application monitoring', 'url': 'https://www.datadoghq.com/'},
                {'name': 'New Relic', 'description': 'Performance monitoring', 'url': 'https://newrelic.com/'}
            ])
        
        return tools

    def _get_security_tools(self, project_type: str) -> List[Dict[str, str]]:
        """Get security tools"""
        tools = [
            {'name': 'OWASP ZAP', 'description': 'Security testing', 'url': 'https://owasp.org/www-project-zap/'},
            {'name': 'SonarQube', 'description': 'Code quality and security', 'url': 'https://www.sonarqube.org/'}
        ]
        
        if project_type in ['web_app', 'api']:
            tools.extend([
                {'name': 'Let\'s Encrypt', 'description': 'Free SSL certificates', 'url': 'https://letsencrypt.org/'},
                {'name': 'Auth0', 'description': 'Authentication service', 'url': 'https://auth0.com/'}
            ])
        
        return tools

    def _get_collaboration_tools(self, complexity: str) -> List[Dict[str, str]]:
        """Get collaboration tools"""
        tools = [
            {'name': 'Slack', 'description': 'Team communication', 'url': 'https://slack.com/'},
            {'name': 'Trello', 'description': 'Project management', 'url': 'https://trello.com/'},
            {'name': 'Notion', 'description': 'Documentation and notes', 'url': 'https://www.notion.so/'}
        ]
        
        if complexity == 'high':
            tools.extend([
                {'name': 'Jira', 'description': 'Advanced project management', 'url': 'https://www.atlassian.com/software/jira'},
                {'name': 'Confluence', 'description': 'Team collaboration', 'url': 'https://www.atlassian.com/software/confluence'}
            ])
        
        return tools

    def _get_learning_resources(self, technologies: List[str], project_type: str) -> List[Dict[str, str]]:
        """Get learning resources"""
        resources = [
            {'name': 'MDN Web Docs', 'description': 'Web development documentation', 'url': 'https://developer.mozilla.org/'},
            {'name': 'Stack Overflow', 'description': 'Developer Q&A community', 'url': 'https://stackoverflow.com/'},
            {'name': 'GitHub', 'description': 'Code examples and projects', 'url': 'https://github.com/'}
        ]
        
        # Technology-specific resources
        if 'python' in technologies:
            resources.extend([
                {'name': 'Real Python', 'description': 'Python tutorials', 'url': 'https://realpython.com/'},
                {'name': 'Python.org', 'description': 'Official Python documentation', 'url': 'https://www.python.org/doc/'}
            ])
        
        if 'javascript' in technologies:
            resources.extend([
                {'name': 'JavaScript.info', 'description': 'Modern JavaScript tutorial', 'url': 'https://javascript.info/'},
                {'name': 'React Docs', 'description': 'Official React documentation', 'url': 'https://reactjs.org/docs/'}
            ])
        
        return resources

    def _generate_coding_prompts(self, design: DesignDocument, ui_design: UIDesignDocument) -> list:
        """Generate coding prompts for each main page/component (frontend/backend/API)"""
        prompts = []
        # Frontend/page prompts
        for layout in ui_design.page_layouts:
            prompts.append({
                'type': 'frontend',
                'target': layout['name'],
                'prompt': (
                    f"Generate the complete frontend code for the '{layout['name']}' page.\n"
                    f"Page type: {layout['type']}.\n"
                    f"Description: {layout['description']}.\n"
                    f"Use the CSS framework: {ui_design.css_framework}.\n"
                    f"Follow the design system: {ui_design.design_system}.\n"
                    f"Make it mobile-friendly and accessible."
                )
            })
        # Backend/API prompts
        for endpoint in design.api_endpoints:
            prompts.append({
                'type': 'backend',
                'target': endpoint['path'],
                'prompt': (
                    f"Generate the backend/API endpoint for '{endpoint['path']}' ({endpoint['method']}).\n"
                    f"Description: {endpoint['description']}.\n"
                    f"Use Python Flask (or your preferred backend framework).\n"
                    f"Ensure proper input validation, authentication, and error handling."
                )
            })
        return prompts

    def _generate_testing_prompts(self, design: DesignDocument, ui_design: UIDesignDocument, plan: ImplementationPlan) -> list:
        """Generate testing prompts for each main feature/component/page"""
        prompts = []
        # Unit tests for backend endpoints
        for endpoint in design.api_endpoints:
            prompts.append({
                'type': 'unit',
                'target': endpoint['path'],
                'prompt': (
                    f"Write unit tests for the API endpoint '{endpoint['path']}' ({endpoint['method']}).\n"
                    f"Test all edge cases, input validation, and error handling.\n"
                    f"Use pytest or unittest in Python."
                )
            })
        # Frontend/component tests
        for layout in ui_design.page_layouts:
            prompts.append({
                'type': 'frontend',
                'target': layout['name'],
                'prompt': (
                    f"Write frontend tests for the '{layout['name']}' page.\n"
                    f"Test all user interactions, form validation, and accessibility.\n"
                    f"Use Jest, React Testing Library, or your preferred tool."
                )
            })
        # E2E tests for main flows
        for phase in plan.phases:
            prompts.append({
                'type': 'e2e',
                'target': phase['name'],
                'prompt': (
                    f"Write end-to-end (E2E) tests for the '{phase['name']}' phase.\n"
                    f"Test the complete user flow described: {phase['description']}.\n"
                    f"Use Cypress, Playwright, or your preferred E2E tool."
                )
            })
        return prompts


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
    
    # Generate UI Design
    ui_design = sdlc_service.generate_ui_design(design, srs, analysis)
    print(f"\nUI Design Generated: {len(ui_design.page_layouts)} pages")
    
    # Generate Implementation Plan
    plan = sdlc_service.generate_implementation_plan(design, analysis, analysis.estimated_hours)
    print(f"\nPlan Generated: {len(plan.tasks)} tasks across {len(plan.phases)} phases")
    
    # Export documents
    files = sdlc_service.export_documents(srs, design, plan, format='markdown')
    print(f"\nDocuments exported: {files}")