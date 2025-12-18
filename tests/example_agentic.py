"""
Example: Using the True Agentic System
"""
from orchestrator_agentic import AgenticOrchestrator
from config import Config

def main():
    """Demonstrate the agentic system."""
    
    print("="*70)
    print("TRUE AGENTIC AI SYSTEM - EXAMPLE")
    print("="*70)
    
    # Initialize the agentic orchestrator
    print("\n1. Initializing agentic system...")
    orchestrator = AgenticOrchestrator(
        deepseek_api_key=Config.DEEPSEEK_API_KEY,
        openai_api_key=Config.OPENAI_API_KEY
    )
    
    # Example 1: Process a PDF document
    print("\n2. Processing PDF document...")
    result1 = orchestrator.process_file(
        file_path='test_data/sample_document.pdf',
        output_dir='output_agentic'
    )
    
    if result1.get('success'):
        print(f"\n✓ Successfully processed PDF")
        print(f"  Category: {result1.get('category')}")
        print(f"  Quality Score: {result1.get('quality_score')}")
        print(f"  Processing Time: {result1.get('processing_time')}s")
    else:
        print(f"\n✗ Failed: {result1.get('error')}")
    
    # Example 2: Process an image
    print("\n3. Processing image...")
    result2 = orchestrator.process_file(
        file_path='test_data/sample_image.jpg',
        output_dir='output_agentic'
    )
    
    if result2.get('success'):
        print(f"\n✓ Successfully processed image")
        print(f"  Category: {result2.get('category')}")
        print(f"  Labels: {list(result2.get('labels', {}).keys())}")
    
    # Get system status
    print("\n4. System Status:")
    status = orchestrator.get_system_status()
    
    print(f"\nAgents:")
    for agent_id, agent_status in status['agents'].items():
        print(f"  {agent_id}: {agent_status['decisions_made']} decisions")
    
    print(f"\nSupervisor:")
    print(f"  Status: {status['supervisor']['status']}")
    print(f"  Decisions: {status['supervisor']['decisions_made']}")
    
    print(f"\nExperience Database:")
    print(f"  Total experiences: {status['experience_db']['total']}")
    if status['experience_db']['total'] > 0:
        print(f"  Average quality: {status['experience_db']['avg_quality']:.2f}")
    
    print(f"\nTools:")
    for tool in status['tools']:
        if tool['usage_count'] > 0:
            print(f"  {tool['name']}: {tool['usage_count']} uses, {tool['success_rate']:.1%} success")
    
    print("\n" + "="*70)
    print("EXAMPLE COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
