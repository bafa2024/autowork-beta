#!/usr/bin/env python3
"""
Test the spam filter with real projects
"""

from spam_filter import SpamFilter
from autowork_minimal import AutoWorkMinimal
import json

def test_spam_filter():
    """Test spam filter on actual projects"""
    print("="*60)
    print("🔍 SPAM FILTER TEST")
    print("="*60)
    
    # Initialize bot and spam filter
    bot = AutoWorkMinimal()
    spam_filter = SpamFilter()
    
    # Fetch some projects
    print("\nFetching projects...")
    projects = bot.get_active_projects(limit=30)
    
    if not projects:
        print("❌ No projects fetched")
        return
    
    print(f"✅ Fetched {len(projects)} projects\n")
    
    spam_count = 0
    legitimate_count = 0
    
    # Test each project
    for i, project in enumerate(projects):
        is_spam, reasons = spam_filter.is_spam(project)
        
        if is_spam:
            spam_count += 1
            print(f"\n🚫 SPAM #{spam_count}: {project.get('title', '')[:60]}...")
            print(f"   Budget: ${project.get('budget', {}).get('minimum', 0)}")
            print(f"   Reasons:")
            for reason in reasons[:3]:  # Show top 3 reasons
                print(f"     - {reason}")
            print(f"   URL: https://www.freelancer.com/projects/{project.get('seo_url', '')}")
        else:
            legitimate_count += 1
    
    # Show summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total projects analyzed: {len(projects)}")
    print(f"Spam projects detected: {spam_count} ({spam_count/len(projects)*100:.1f}%)")
    print(f"Legitimate projects: {legitimate_count} ({legitimate_count/len(projects)*100:.1f}%)")
    
    # Show detailed stats
    stats = spam_filter.get_stats()
    if stats['top_reasons']:
        print(f"\nTop spam indicators:")
        for reason, count in stats['top_reasons']:
            print(f"  - {reason}: {count} occurrences")

def test_specific_examples():
    """Test with specific spam examples"""
    print("\n" + "="*60)
    print("🧪 TESTING SPECIFIC SPAM EXAMPLES")
    print("="*60)
    
    spam_filter = SpamFilter()
    
    # Test cases
    test_projects = [
        {
            'id': 1,
            'title': 'EARN $500 PER DAY FROM HOME!!!',
            'description': 'Simple data entry job. Contact me on WhatsApp +1234567890',
            'budget': {'minimum': 500, 'maximum': 1000},
            'bid_stats': {'bid_count': 2}
        },
        {
            'id': 2,
            'title': 'Need Python developer for web scraping',
            'description': 'I need a Python developer to create a web scraping script for extracting product data from e-commerce sites. The script should handle pagination, save data to CSV, and include error handling. Please provide examples of similar work.',
            'budget': {'minimum': 100, 'maximum': 300},
            'bid_stats': {'bid_count': 15}
        },
        {
            'id': 3,
            'title': 'Buy Instagram Followers - 10K for $50',
            'description': 'Need someone to provide 10,000 Instagram followers quickly',
            'budget': {'minimum': 50, 'maximum': 50},
            'bid_stats': {'bid_count': 0}
        },
        {
            'id': 4,
            'title': 'Academic Writing - Dissertation Help',
            'description': 'Write my dissertation on machine learning. 50 pages needed.',
            'budget': {'minimum': 1000, 'maximum': 2000},
            'bid_stats': {'bid_count': 5}
        }
    ]
    
    for project in test_projects:
        is_spam, reasons = spam_filter.is_spam(project)
        print(f"\nProject: {project['title']}")
        print(f"Result: {'🚫 SPAM' if is_spam else '✅ LEGITIMATE'}")
        if reasons:
            print("Reasons:")
            for reason in reasons:
                print(f"  - {reason}")

if __name__ == "__main__":
    # Test with real projects
    test_spam_filter()
    
    # Test with examples
    test_specific_examples()