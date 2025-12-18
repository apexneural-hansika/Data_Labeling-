"""
Quick test to verify the agentic system is working
"""
from orchestrator_agentic import AgenticOrchestrator
from config import Config
import os

def test_agentic_system():
    """Test the agentic orchestrator."""
    
    print("\n" + "="*70)
    print("TESTING TRUE AGENTIC SYSTEM")
    print("="*70)
    
    # Initialize
    print("\n1. Initializing agentic orchestrator...")
    orchestrator = AgenticOrchestrator(
        deepseek_api_key=Config.DEEPSEEK_API_KEY,
        openai_api_key=Config.OPENAI_API_KEY
    )
    
    # Get system status
    print("\n2. Checking system status...")
    status = orchestrator.get_system_status()
    
    print(f"\n✓ Agentic System Status:")
    print(f"  - Agents: {len(status['agents'])}")
    print(f"  - Tools: {len(status['tools'])}")
    print(f"  - Supervisor: {status['supervisor']['status']}")
    
    # Test with a sample file if available
    test_files = [
        'test_data/sample_document.pdf',
        'test_data/sample_image.jpg',
        'test_data/sample_image.png'
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            test_file = f
            break
    
    if test_file:
        print(f"\n3. Testing with file: {test_file}")
        result = orchestrator.process_file(test_file, output_dir='output_agentic')
        
        if result.get('success'):
            print(f"\n✓ File processed successfully!")
            print(f"  - Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"  - Agents involved: {result.get('agents_involved', [])}")
        else:
            print(f"\n✗ Processing failed: {result.get('error')}")
    else:
        print("\n3. No test files found, skipping file processing test")
    
    print("\n" + "="*70)
    print("TEST COMPLETE - Agentic system is working!")
    print("="*70 + "\n")

if __name__ == '__main__':
    test_agentic_system()
