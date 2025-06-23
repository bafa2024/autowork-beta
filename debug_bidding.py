#!/usr/bin/env python3
"""
Debug script to find out why bids aren't being placed
"""

import logging
from autowork_minimal import AutoWorkMinimal

# Set debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DebugBot(AutoWorkMinimal):
    """Debug version with detailed logging"""
    
    def __init__(self):
        super().__init__()
        self.debug_stats = {
            'projects_fetched': 0,
            'projects_analyzed': 0,
            'skip_reasons': {}
        }
    
    def should_bid_on_project(self, project):
        """Override with detailed logging"""
        self.debug_stats['projects_analyzed'] += 1
        project_id = project.get('id')
        title = project.get('title', 'Unknown')[:50]
        
        print(f"\n{'='*60}")
        print(f"🔍 ANALYZING PROJECT: {title}")
        print(f"   ID: {project_id}")
        
        # Check already processed
        if project_id in self.processed_projects:
            reason = "Already processed"
            self.track_skip_reason(reason)
            print(f"   ❌ SKIP: {reason}")
            return False, reason
        
        # Get project details
        bid_stats = project.get('bid_stats', {})
        bid_count = bid_stats.get('bid_count', 0) if isinstance(bid_stats, dict) else 0
        
        budget = project.get('budget', {})
        min_budget = float(budget.get('minimum', 0)) if isinstance(budget, dict) else 0
        max_budget = float(budget.get('maximum', 0)) if isinstance(budget, dict) else 0
        
        # Print project info
        print(f"   💰 Budget: ${min_budget} - ${max_budget}")
        print(f"   🏷️ Bids: {bid_count}")
        print(f"   🎯 Skills: {', '.join([j.get('name', '') for j in project.get('jobs', [])[:3]])}")
        
        # Check bid count
        max_bids = self.config['filtering']['skip_projects_with_bids_above']
        print(f"   📊 Bid count check: {bid_count} <= {max_bids}?", end=" ")
        if bid_count > max_bids:
            reason = f"Too many bids ({bid_count} > {max_bids})"
            self.track_skip_reason(reason)
            print(f"❌ FAIL")
            print(f"   ❌ SKIP: {reason}")
            return False, reason
        print("✅ PASS")
        
        # Check budget
        min_profitable = self.config['smart_bidding']['min_profitable_budget']
        print(f"   💵 Budget check: ${min_budget} >= ${min_profitable}?", end=" ")
        if min_budget < min_profitable:
            reason = f"Budget too low (${min_budget} < ${min_profitable})"
            self.track_skip_reason(reason)
            print(f"❌ FAIL")
            print(f"   ❌ SKIP: {reason}")
            return False, reason
        print("✅ PASS")
        
        # Check client (if enabled)
        if self.config['client_filtering']['enabled']:
            print(f"   👤 Client check: ", end="")
            employer_id = project.get('owner_id')
            if employer_id:
                client_analysis = self.analyze_client(employer_id)
                if not client_analysis.get('is_good_client', True):
                    reason = "Client doesn't meet criteria"
                    self.track_skip_reason(reason)
                    print(f"❌ FAIL")
                    print(f"   ❌ SKIP: {reason}")
                    return False, reason
            print("✅ PASS (or disabled)")
        
        # Check skill match (if enabled)
        if self.config['filtering']['portfolio_matching']:
            match_score = self.calculate_skill_match(project)
            min_score = self.config['filtering']['min_skill_match_score']
            print(f"   🎯 Skill match: {match_score:.2f} >= {min_score}?", end=" ")
            if match_score < min_score:
                reason = f"Poor skill match ({match_score:.2f} < {min_score})"
                self.track_skip_reason(reason)
                print(f"❌ FAIL")
                print(f"   ❌ SKIP: {reason}")
                return False, reason
            print("✅ PASS")
        
        print(f"   ✅ PROJECT APPROVED FOR BIDDING!")
        return True, "Good opportunity"
    
    def track_skip_reason(self, reason):
        """Track why projects are skipped"""
        if reason not in self.debug_stats['skip_reasons']:
            self.debug_stats['skip_reasons'][reason] = 0
        self.debug_stats['skip_reasons'][reason] += 1
    
    def run_debug_cycle(self):
        """Run one cycle with detailed debugging"""
        print("\n" + "="*60)
        print("🐛 DEBUG MODE - ANALYZING WHY BIDS AREN'T BEING PLACED")
        print("="*60)
        
        print("\n📋 Current Configuration:")
        print(f"   Min budget: ${self.config['smart_bidding']['min_profitable_budget']}")
        print(f"   Max bids allowed: {self.config['filtering']['skip_projects_with_bids_above']}")
        print(f"   Client filtering: {'Enabled' if self.config['client_filtering']['enabled'] else 'Disabled'}")
        print(f"   Portfolio matching: {'Enabled' if self.config['filtering']['portfolio_matching'] else 'Disabled'}")
        
        # Fetch projects
        print("\n🔄 Fetching projects...")
        projects = self.get_active_projects(limit=20)
        self.debug_stats['projects_fetched'] = len(projects)
        
        if not projects:
            print("❌ No projects fetched! Check your token.")
            return
        
        print(f"✅ Fetched {len(projects)} projects")
        
        # Analyze each project
        approved_count = 0
        for i, project in enumerate(projects[:10]):  # Analyze first 10
            should_bid, reason = self.should_bid_on_project(project)
            if should_bid:
                approved_count += 1
                print(f"\n🎯 Would attempt to bid on this project!")
        
        # Summary
        print("\n" + "="*60)
        print("📊 DEBUG SUMMARY")
        print("="*60)
        print(f"Projects fetched: {self.debug_stats['projects_fetched']}")
        print(f"Projects analyzed: {self.debug_stats['projects_analyzed']}")
        print(f"Projects approved for bidding: {approved_count}")
        
        if self.debug_stats['skip_reasons']:
            print("\n❌ Skip Reasons:")
            for reason, count in sorted(self.debug_stats['skip_reasons'].items(), key=lambda x: x[1], reverse=True):
                print(f"   {reason}: {count}")
        
        if approved_count == 0:
            print("\n⚠️  NO PROJECTS APPROVED FOR BIDDING!")
            print("\n💡 Suggestions:")
            print("1. Lower min_profitable_budget in bot_config.json")
            print("2. Increase skip_projects_with_bids_above")
            print("3. Disable client_filtering if enabled")
            print("4. Disable portfolio_matching if enabled")
            print("5. Check if your skills match any projects")

if __name__ == "__main__":
    bot = DebugBot()
    bot.run_debug_cycle()