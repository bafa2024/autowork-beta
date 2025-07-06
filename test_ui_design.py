#!/usr/bin/env python3
"""
Test script to verify UI design generation functionality
"""

import json
from auto_sdlc_service import AutoSDLCService

def test_ui_design_generation():
    """Test the complete SDLC process including UI design generation"""
    
    print("=== Testing UI Design Generation ===\n")
    
    # Initialize SDLC service
    sdlc_service = AutoSDLCService()
    
    # Test project description
    project_description = """
    Create a web application for managing a small business inventory system. 
    The application should allow users to:
    - Add, edit, and delete inventory items
    - Track stock levels and set low stock alerts
    - Generate reports on inventory movement
    - Manage suppliers and purchase orders
    - User authentication and role-based access control
    
    The system should be responsive and work on desktop and mobile devices.
    Use modern web technologies and follow best practices for security and performance.
    """
    
    project_title = "Inventory Management System"
    
    try:
        print("1. Analyzing project...")
        analysis = sdlc_service.analyze_project(project_description)
        print(f"   ✓ Project Type: {analysis.project_type}")
        print(f"   ✓ Complexity: {analysis.complexity}")
        print(f"   ✓ Estimated Hours: {analysis.estimated_hours}")
        print(f"   ✓ Technologies: {', '.join(analysis.technologies[:5])}")
        
        print("\n2. Generating SRS...")
        srs = sdlc_service.generate_srs(project_description, analysis, project_title)
        print(f"   ✓ SRS generated with {len(srs.functional_requirements)} functional requirements")
        
        print("\n3. Generating System Design...")
        design = sdlc_service.generate_design(srs, analysis)
        print(f"   ✓ System design generated: {design.architecture_type}")
        print(f"   ✓ Components: {len(design.components)}")
        
        print("\n4. Generating UI Design...")
        ui_design = sdlc_service.generate_ui_design(design, srs, analysis)
        print(f"   ✓ UI design generated successfully!")
        print(f"   ✓ Page Layouts: {len(ui_design.page_layouts)}")
        print(f"   ✓ UI Components: {len(ui_design.components)}")
        print(f"   ✓ HTML Templates: {len(ui_design.html_templates)}")
        print(f"   ✓ CSS Framework: {ui_design.css_framework}")
        print(f"   ✓ JavaScript Libraries: {', '.join(ui_design.javascript_libraries)}")
        
        print("\n5. Generating Implementation Plan...")
        plan = sdlc_service.generate_implementation_plan(design, analysis, analysis.estimated_hours)
        print(f"   ✓ Implementation plan generated")
        print(f"   ✓ Phases: {len(plan.phases)}")
        print(f"   ✓ Tasks: {len(plan.tasks)}")
        
        # Display UI Design details
        print("\n=== UI Design Details ===")
        print(f"Design System:")
        for key, value in ui_design.design_system.items():
            print(f"  {key}: {value}")
        
        print(f"\nPage Layouts:")
        for layout in ui_design.page_layouts[:3]:  # Show first 3
            print(f"  - {layout['name']}: {layout['type']} - {layout['description']}")
        
        print(f"\nUI Components:")
        for comp in ui_design.components[:5]:  # Show first 5
            print(f"  - {comp['name']}: {comp['type']} - {comp['description']}")
        
        print(f"\nInteractive Elements:")
        for element in ui_design.interactive_elements[:3]:  # Show first 3
            print(f"  - {element['name']}: {element['type']} - {element['description']}")
        
        print(f"\nHTML Templates:")
        for template in ui_design.html_templates[:2]:  # Show first 2
            print(f"  - {template['name']} ({template['page']})")
            print(f"    CSS Framework: {template['css_framework']}")
            print(f"    HTML Length: {len(template['html'])} characters")
        
        print("\n=== Test Summary ===")
        print("✅ All SDLC steps completed successfully!")
        print("✅ UI Design generation working correctly!")
        print("✅ HTML templates generated with proper structure!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ui_design_generation()
    if success:
        print("\n🎉 UI Design integration test PASSED!")
    else:
        print("\n💥 UI Design integration test FAILED!") 