"""
Test script to verify the application is working correctly
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

def test_imports():
    """Test that all imports work correctly."""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    try:
        from app import app
        print("[OK] Flask app imports successfully")
    except Exception as e:
        print(f"[FAIL] Failed to import app: {e}")
        return False
    
    try:
        from orchestrator_agentic import AgenticOrchestrator
        print("[OK] Orchestrator imports successfully")
    except Exception as e:
        print(f"[FAIL] Failed to import orchestrator: {e}")
        return False
    
    try:
        from config import Config
        print("[OK] Config imports successfully")
    except Exception as e:
        print(f"[FAIL] Failed to import config: {e}")
        return False
    
    try:
        from agents.agentic_core.memory import AgentMemory
        print("[OK] Agentic core imports successfully")
    except Exception as e:
        print(f"[FAIL] Failed to import agentic_core: {e}")
        return False
    
    try:
        from agents.agentic_agents.supervisor import SupervisorAgent
        print("[OK] Agentic agents imports successfully")
    except Exception as e:
        print(f"[FAIL] Failed to import agentic_agents: {e}")
        return False
    
    return True

def test_flask_routes():
    """Test Flask routes."""
    print("\n" + "=" * 60)
    print("TESTING FLASK ROUTES")
    print("=" * 60)
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            if response.status_code == 200:
                print("[OK] Home route (/) works")
            else:
                print(f"[FAIL] Home route failed: {response.status_code}")
                return False
            
            # Test health check
            response = client.get('/api/health')
            if response.status_code == 200:
                print("[OK] Health check route (/api/health) works")
                data = response.get_json()
                print(f"  Status: {data.get('status', 'unknown')}")
            else:
                print(f"[FAIL] Health check failed: {response.status_code}")
                return False
            
            # Test stats route
            response = client.get('/api/stats')
            if response.status_code == 200:
                print("[OK] Stats route (/api/stats) works")
            else:
                print(f"[FAIL] Stats route failed: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Flask route test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    try:
        from config import Config
        
        is_valid, error_msg = Config.validate()
        if is_valid:
            print("[OK] Configuration is valid")
            print(f"  OpenAI API Key: {'Set' if Config.OPENAI_API_KEY else 'Not set'}")
            print(f"  DeepSeek API Key: {'Set' if Config.DEEPSEEK_API_KEY else 'Not set'}")
            print(f"  Upload Folder: {Config.UPLOAD_FOLDER}")
            return True
        else:
            print(f"[FAIL] Configuration invalid: {error_msg}")
            return False
    except Exception as e:
        print(f"[FAIL] Config test failed: {e}")
        return False

def test_orchestrator_init():
    """Test orchestrator initialization."""
    print("\n" + "=" * 60)
    print("TESTING ORCHESTRATOR INITIALIZATION")
    print("=" * 60)
    
    try:
        from orchestrator_agentic import AgenticOrchestrator
        from config import Config
        
        print("Initializing orchestrator...")
        orchestrator = AgenticOrchestrator(
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            openai_api_key=Config.OPENAI_API_KEY
        )
        print("[OK] Orchestrator initialized successfully")
        
        # Get system status
        status = orchestrator.get_system_status()
        print(f"  Agents: {len(status.get('agents', {}))}")
        print(f"  Tools: {len(status.get('tools', []))}")
        print(f"  Supervisor status: {status.get('supervisor', {}).get('status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Orchestrator initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("RUNNING APPLICATION TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Flask Routes", test_flask_routes()))
    results.append(("Orchestrator", test_orchestrator_init()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Application is working correctly.")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed. Please check the errors above.")
        sys.exit(1)

