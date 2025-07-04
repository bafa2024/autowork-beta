#!/usr/bin/env python3
"""
Integration module for Auto SDLC Service with AutoWork Bot
Automatically analyzes projects and generates documentation before bidding
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from auto_sdlc_service import (
    AutoSDLCService, 
    ProjectAnalysis, 
    SRSDocument, 
    DesignDocument, 
    ImplementationPlan
)

class SDLCBotIntegration:
    def __init__(self, bot_instance):
        """
        Initialize SDLC integration with bot
        
        Args:
            bot_instance: Instance of AutoWorkMinimal bot
        """
        self.bot = bot_instance
        self.sdlc_service = AutoSDLCService(ai_provider=self._get_ai_provider())
        
        # Storage for analyzed projects
        self.analyzed_projects = {}
        self.sdlc_cache_file = 'sdlc_analysis_cache.json'
        self._load_cache()
        
        # Configuration
        self.config = self._load_sdlc_config()
        
        logging.info("✓ SDLC Integration initialized")
    
    def _get_ai_provider(self) -> str:
        """Determine which AI provider to use based on available API keys"""
        if os.environ.get('OPENAI_API_KEY'):
            return 'openai'
        elif os.environ.get('ANTHROPIC_API_KEY'):
            return 'anthropic'
        elif os.environ.get('GOOGLE_API_KEY'):
            return 'gemini'
        else:
            logging.warning("No AI API key found. SDLC service will use template-based generation.")
            return 'openai'  # Default, will use templates
    
    def _load_sdlc_config(self) -> Dict:
        """Load SDLC-specific configuration"""
        default_config = {
            'auto_analyze': True,
            'generate_on_bid': True,
            'complexity_thresholds': {
                'low': {'max_hours': 80, 'min_budget': 100},
                'medium': {'max_hours': 200, 'min_budget': 500},
                'high': {'max_hours': 500, 'min_budget': 2000}
            },
            'document_formats': ['json', 'markdown'],
            'include_in_bid': True,
            'ai_enhanced_bids': True
        }
        
        # Try to load from bot config
        if hasattr(self.bot, 'config') and 'sdlc' in self.bot.config:
            default_config.update(self.bot.config['sdlc'])
        
        return default_config
    
    def _load_cache(self):
        """Load cached SDLC analyses"""
        if os.path.exists(self.sdlc_cache_file):
            try:
                with open(self.sdlc_cache_file, 'r') as f:
                    self.analyzed_projects = json.load(f)
            except Exception as e:
                logging.warning(f"Could not load SDLC cache: {e}")
    
    def _save_cache(self):
        """Save SDLC analyses to cache"""
        try:
            with open(self.sdlc_cache_file, 'w') as f:
                json.dump(self.analyzed_projects, f, indent=2)
        except Exception as e:
            logging.warning(f"Could not save SDLC cache: {e}")
    
    def should_analyze_project(self, project: Dict) -> bool:
        """
        Determine if project should go through SDLC analysis
        
        Args:
            project: Project data from Freelancer
            
        Returns:
            bool: True if project should be analyzed
        """
        if not self.config['auto_analyze']:
            return False
        
        # Check if already analyzed
        project_id = str(project.get('id'))
        if project_id in self.analyzed_projects:
            return False
        
        # Check project type and budget
        budget = project.get('budget', {})
        if isinstance(budget, dict):
            min_budget = budget.get('minimum', 0)
            
            # Only analyze projects above certain budget
            if min_budget < self.config['complexity_thresholds']['low']['min_budget']:
                return False
        
        # Check if it's a development project
        description = project.get('description', '').lower()
        title = project.get('title', '').lower()
        
        dev_keywords = [
            'develop', 'build', 'create', 'application', 'website', 'app',
            'system', 'platform', 'software', 'api', 'backend', 'frontend'
        ]
        
        if any(keyword in description + title for keyword in dev_keywords):
            return True
        
        return False
    
    def analyze_and_generate_docs(self, project: Dict) -> Optional[Dict]:
        """
        Analyze project and generate SDLC documents
        
        Args:
            project: Project data from Freelancer
            
        Returns:
            Dict with analysis and documents, or None if failed
        """
        project_id = str(project.get('id'))
        
        # Check cache first
        if project_id in self.analyzed_projects:
            logging.info(f"Using cached SDLC analysis for project {project_id}")
            return self.analyzed_projects[project_id]
        
        try:
            logging.info(f"🔍 Running SDLC analysis for project: {project.get('title', '')[:50]}...")
            
            # Extract project info
            description = project.get('description', '')
            title = project.get('title', 'Project')
            budget = project.get('budget', {})
            
            # Step 1: Analyze project
            analysis = self.sdlc_service.analyze_project(description, budget)
            
            # Step 2: Generate SRS
            srs = self.sdlc_service.generate_srs(description, analysis, title)
            
            # Step 3: Generate Design
            design = self.sdlc_service.generate_design(srs, analysis)
            
            # Step 4: Generate Implementation Plan
            plan = self.sdlc_service.generate_implementation_plan(
                design, analysis, analysis.estimated_hours
            )
            
            # Step 5: Export documents
            files = {}
            for format in self.config['document_formats']:
                format_files = self.sdlc_service.export_documents(
                    srs, design, plan, format=format
                )
                files.update(format_files)
            
            # Create result
            result = {
                'project_id': project_id,
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis.__dict__,
                'srs_summary': {
                    'title': srs.project_title,
                    'overview': srs.overview,
                    'requirements_count': len(srs.functional_requirements),
                    'user_stories_count': len(srs.user_stories)
                },
                'design_summary': {
                    'architecture': design.architecture_type,
                    'components_count': len(design.components),
                    'tech_stack': design.technology_stack
                },
                'plan_summary': {
                    'phases': len(plan.phases),
                    'tasks': len(plan.tasks),
                    'timeline': plan.timeline,
                    'developers_needed': plan.resource_allocation.get('developers', 1)
                },
                'files': files,
                'full_docs': {
                    'srs': srs.__dict__,
                    'design': design.__dict__,
                    'plan': plan.__dict__
                }
            }
            
            # Cache result
            self.analyzed_projects[project_id] = result
            self._save_cache()
            
            logging.info(f"✓ SDLC analysis complete for project {project_id}")
            return result
            
        except Exception as e:
            logging.error(f"Error in SDLC analysis: {e}")
            return None
    
    def enhance_bid_message(self, project: Dict, base_message: str, 
                           sdlc_analysis: Dict) -> str:
        """
        Enhance bid message with SDLC insights
        
        Args:
            project: Project data
            base_message: Original bid message
            sdlc_analysis: SDLC analysis results
            
        Returns:
            Enhanced bid message
        """
        if not self.config['include_in_bid']:
            return base_message
        
        try:
            analysis = sdlc_analysis['analysis']
            plan = sdlc_analysis['plan_summary']
            
            # Create enhancement
            enhancement = f"\n\n**Project Analysis & Approach:**\n"
            enhancement += f"• Project Type: {analysis['project_type'].replace('_', ' ').title()}\n"
            enhancement += f"• Complexity: {analysis['complexity'].title()}\n"
            enhancement += f"• Estimated Timeline: {plan['timeline']['total_weeks']} weeks\n"
            enhancement += f"• Development Phases: {plan['phases']}\n"
            
            if analysis['technologies']:
                enhancement += f"• Recommended Tech: {', '.join(analysis['technologies'][:5])}\n"
            
            enhancement += f"\nI've prepared a detailed project plan with {plan['tasks']} tasks "
            enhancement += f"and clear milestones. Happy to share the full technical documentation.\n"
            
            # Add to base message
            enhanced_message = base_message + enhancement
            
            # Ensure it's not too long (Freelancer has limits)
            if len(enhanced_message) > 4000:
                enhanced_message = enhanced_message[:3997] + "..."
            
            return enhanced_message
            
        except Exception as e:
            logging.warning(f"Could not enhance bid message: {e}")
            return base_message
    
    def get_bid_amount_recommendation(self, project: Dict, sdlc_analysis: Dict) -> float:
        """
        Get recommended bid amount based on SDLC analysis
        
        Args:
            project: Project data
            sdlc_analysis: SDLC analysis results
            
        Returns:
            Recommended bid amount
        """
        try:
            analysis = sdlc_analysis['analysis']
            hours = analysis['estimated_hours']
            complexity = analysis['complexity']
            
            # Base hourly rates by complexity
            hourly_rates = {
                'low': 25,
                'medium': 50,
                'high': 75
            }
            
            base_rate = hourly_rates.get(complexity, 50)
            
            # Adjust based on technologies
            if 'blockchain' in analysis['technologies'] or 'ml' in analysis['technologies']:
                base_rate *= 1.5
            elif 'react' in analysis['technologies'] or 'node' in analysis['technologies']:
                base_rate *= 1.2
            
            # Calculate total
            recommended = hours * base_rate
            
            # Compare with project budget
            budget = project.get('budget', {})
            if isinstance(budget, dict):
                min_budget = budget.get('minimum', 0)
                max_budget = budget.get('maximum', 0)
                
                # Stay within budget range
                if recommended < min_budget:
                    recommended = min_budget
                elif max_budget > 0 and recommended > max_budget:
                    recommended = max_budget * 0.9  # Slightly under max
            
            return recommended
            
        except Exception as e:
            logging.warning(f"Could not calculate bid recommendation: {e}")
            return None
    
    def generate_proposal_document(self, project: Dict, sdlc_analysis: Dict) -> str:
        """
        Generate a professional proposal document
        
        Args:
            project: Project data
            sdlc_analysis: SDLC analysis results
            
        Returns:
            Path to proposal document
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"proposal_{project.get('id')}_{timestamp}.md"
            
            analysis = sdlc_analysis['analysis']
            srs_summary = sdlc_analysis['srs_summary']
            design_summary = sdlc_analysis['design_summary']
            plan_summary = sdlc_analysis['plan_summary']
            
            proposal = f"""# Project Proposal: {project.get('title', 'Project')}

## Executive Summary

I am pleased to submit this comprehensive proposal for your {analysis['project_type'].replace('_', ' ')} project. 
Based on my analysis, this is a {analysis['complexity']} complexity project that will require approximately 
{analysis['estimated_hours']} hours of development effort.

## Project Understanding

{srs_summary['overview']}

### Key Features Identified
{chr(10).join([f"- {feature}" for feature in analysis['key_features'][:5]])}

## Technical Approach

### Architecture
{design_summary['architecture']}

### Technology Stack
- **Frontend**: {', '.join(design_summary['tech_stack'].get('frontend', ['TBD']))}
- **Backend**: {', '.join(design_summary['tech_stack'].get('backend', ['TBD']))}
- **Database**: {', '.join(design_summary['tech_stack'].get('database', ['TBD']))}

## Development Plan

### Timeline
- **Total Duration**: {plan_summary['timeline']['total_weeks']} weeks
- **Total Hours**: {plan_summary['timeline']['total_hours']} hours
- **Phases**: {plan_summary['phases']}
- **Tasks**: {plan_summary['tasks']}

### Development Phases
{chr(10).join([f"{i+1}. **{phase['name']}** - {phase['hours']} hours ({phase['days']} days)" 
              for i, phase in enumerate(plan_summary['timeline']['phases'][:4])])}

## Risk Mitigation

### Identified Risks
{chr(10).join([f"- {risk}" for risk in analysis['risks']])}

### Mitigation Strategies
- Regular progress updates and demos
- Comprehensive testing at each phase
- Clear documentation throughout
- Agile development approach for flexibility

## Why Choose Me

- Proven expertise in {', '.join(analysis['technologies'][:3])} development
- Systematic approach with detailed planning
- Commitment to quality and timely delivery
- Clear communication throughout the project

## Investment

Based on the project complexity and requirements, the estimated investment is within your budget range.
I'm happy to discuss the specifics and any adjustments needed.

## Next Steps

1. Review this proposal and technical documentation
2. Discuss any clarifications or modifications
3. Finalize timeline and milestones
4. Begin development

I look forward to bringing your vision to life!

---
*This proposal includes comprehensive technical documentation (SRS, Design, Implementation Plan) available upon request.*
"""
            
            # Save proposal
            with open(filename, 'w') as f:
                f.write(proposal)
            
            logging.info(f"✓ Proposal document generated: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error generating proposal: {e}")
            return None
    
    def integrate_with_bot_workflow(self):
        """
        Integrate SDLC analysis into bot's bidding workflow
        This modifies the bot's should_bid_on_project method
        """
        # Store original method
        original_should_bid = self.bot.should_bid_on_project
        
        def enhanced_should_bid(project):
            # First, check original criteria
            should_bid, reason = original_should_bid(project)
            
            if not should_bid:
                return should_bid, reason
            
            # If original says yes, check if we should analyze
            if self.should_analyze_project(project):
                logging.info("🤖 Running SDLC analysis before bidding...")
                
                sdlc_result = self.analyze_and_generate_docs(project)
                
                if sdlc_result:
                    analysis = sdlc_result['analysis']
                    
                    # Additional filtering based on SDLC analysis
                    if analysis['complexity'] == 'high' and analysis['estimated_hours'] > 400:
                        complexity_budget = self.config['complexity_thresholds']['high']['min_budget']
                        budget_min = project.get('budget', {}).get('minimum', 0)
                        
                        if budget_min < complexity_budget:
                            return False, f"High complexity project with insufficient budget"
                    
                    # Store analysis for later use
                    project['_sdlc_analysis'] = sdlc_result
                    
                    return True, f"{reason} + SDLC analysis complete"
            
            return should_bid, reason
        
        # Replace method
        self.bot.should_bid_on_project = enhanced_should_bid
        logging.info("✓ SDLC workflow integrated with bot")
    
    def integrate_bid_enhancement(self):
        """
        Integrate bid message enhancement into bot's workflow
        """
        # Store original method
        original_select_bid = self.bot.select_bid_message
        
        def enhanced_select_bid(project):
            # Get original message
            base_message = original_select_bid(project)
            
            # Check if we have SDLC analysis
            if hasattr(project, '_sdlc_analysis') or '_sdlc_analysis' in project:
                sdlc_analysis = project.get('_sdlc_analysis')
                if sdlc_analysis:
                    # Enhance the message
                    enhanced_message = self.enhance_bid_message(project, base_message, sdlc_analysis)
                    
                    # Generate proposal if configured
                    if self.config.get('generate_proposal', True):
                        proposal_path = self.generate_proposal_document(project, sdlc_analysis)
                        if proposal_path:
                            enhanced_message += f"\n\n📎 Detailed proposal document available."
                    
                    return enhanced_message
            
            return base_message
        
        # Replace method
        self.bot.select_bid_message = enhanced_select_bid
        logging.info("✓ Bid enhancement integrated with bot")
    
    def integrate_bid_amount_recommendation(self):
        """
        Integrate bid amount recommendation into bot's workflow
        """
        # Store original method
        original_calculate_bid = self.bot.calculate_bid_amount
        
        def enhanced_calculate_bid(project):
            # Check if we have SDLC analysis
            if hasattr(project, '_sdlc_analysis') or '_sdlc_analysis' in project:
                sdlc_analysis = project.get('_sdlc_analysis')
                if sdlc_analysis:
                    # Get recommendation
                    recommended = self.get_bid_amount_recommendation(project, sdlc_analysis)
                    if recommended:
                        logging.info(f"💰 SDLC recommended bid: ${recommended:.2f}")
                        
                        # You can choose to use the recommendation or the original
                        # For now, we'll average them
                        original_amount = original_calculate_bid(project)
                        final_amount = (recommended + original_amount) / 2
                        
                        return final_amount
            
            return original_calculate_bid(project)
        
        # Replace method
        self.bot.calculate_bid_amount = enhanced_calculate_bid
        logging.info("✓ Bid amount recommendation integrated with bot")
    
    def get_project_insights(self, project_id: str) -> Optional[Dict]:
        """
        Get SDLC insights for a specific project
        
        Args:
            project_id: Project ID
            
        Returns:
            SDLC analysis if available
        """
        return self.analyzed_projects.get(str(project_id))
    
    def generate_weekly_report(self) -> str:
        """
        Generate weekly report of SDLC analyses
        
        Returns:
            Path to report file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sdlc_weekly_report_{timestamp}.md"
            
            # Group analyses by complexity
            by_complexity = {'low': [], 'medium': [], 'high': []}
            total_hours = 0
            
            for project_id, analysis in self.analyzed_projects.items():
                complexity = analysis['analysis']['complexity']
                by_complexity[complexity].append(analysis)
                total_hours += analysis['analysis']['estimated_hours']
            
            report = f"""# SDLC Analysis Weekly Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Projects Analyzed: {len(self.analyzed_projects)}
- Total Development Hours: {total_hours:,}
- Average Hours per Project: {total_hours / len(self.analyzed_projects):.0f}

## Complexity Distribution
- Low Complexity: {len(by_complexity['low'])} projects
- Medium Complexity: {len(by_complexity['medium'])} projects  
- High Complexity: {len(by_complexity['high'])} projects

## Technology Trends
"""
            
            # Analyze technology trends
            tech_count = {}
            for analysis in self.analyzed_projects.values():
                for tech in analysis['analysis']['technologies']:
                    tech_count[tech] = tech_count.get(tech, 0) + 1
            
            # Sort by frequency
            sorted_tech = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)
            
            report += "\n### Most Requested Technologies\n"
            for tech, count in sorted_tech[:10]:
                report += f"- {tech}: {count} projects\n"
            
            report += "\n## Project Types\n"
            
            # Analyze project types
            type_count = {}
            for analysis in self.analyzed_projects.values():
                ptype = analysis['analysis']['project_type']
                type_count[ptype] = type_count.get(ptype, 0) + 1
            
            for ptype, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
                report += f"- {ptype.replace('_', ' ').title()}: {count} projects\n"
            
            # Save report
            with open(filename, 'w') as f:
                f.write(report)
            
            logging.info(f"✓ Weekly report generated: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error generating weekly report: {e}")
            return None


def integrate_sdlc_with_bot(bot_instance):
    """
    Main integration function to add SDLC capabilities to bot
    
    Args:
        bot_instance: Instance of AutoWorkMinimal bot
        
    Returns:
        SDLCBotIntegration instance
    """
    # Create integration
    integration = SDLCBotIntegration(bot_instance)
    
    # Integrate all features
    integration.integrate_with_bot_workflow()
    integration.integrate_bid_enhancement()
    integration.integrate_bid_amount_recommendation()
    
    # Add SDLC commands to bot
    bot_instance.sdlc_integration = integration
    
    logging.info("✅ SDLC Service fully integrated with AutoWork bot")
    return integration


# Add SDLC configuration to bot_config.json
SDLC_CONFIG_ADDITION = {
    "sdlc": {
        "enabled": True,
        "auto_analyze": True,
        "generate_on_bid": True,
        "ai_provider": "openai",
        "complexity_thresholds": {
            "low": {"max_hours": 80, "min_budget": 100},
            "medium": {"max_hours": 200, "min_budget": 500},
            "high": {"max_hours": 500, "min_budget": 2000}
        },
        "document_formats": ["json", "markdown"],
        "include_in_bid": True,
        "ai_enhanced_bids": True,
        "generate_proposal": True,
        "min_budget_for_analysis": 500
    }
}