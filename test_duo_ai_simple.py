#!/usr/bin/env python3
"""
Simple test for Duo AI system components
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_message_types():
    """Test message types"""
    print("Testing message types...")
    
    try:
        from agents.message_types import (
            AgentMessage, ProjectPhaseMessage, ImplementationStatusMessage,
            TaskAssignmentMessage, GuidanceRequestMessage, ImplementationResultMessage,
            ConversationMessage
        )
        
        # Test AgentMessage
        msg = AgentMessage(
            sender="test",
            recipient="test",
            message_type="test_type",
            content={"test": "data"}
        )
        print(f"✅ AgentMessage created: {msg.sender} -> {msg.recipient}")
        
        # Test ProjectPhaseMessage
        phase_msg = ProjectPhaseMessage(
            phase="planning",
            guidance={"test": "guidance"},
            success_criteria=["criteria1", "criteria2"]
        )
        print(f"✅ ProjectPhaseMessage created: {phase_msg.phase}")
        
        # Test ConversationMessage
        conv_msg = ConversationMessage(
            conversation_id="test_conv",
            message="Test message",
            context={"test": "context"}
        )
        print(f"✅ ConversationMessage created: {conv_msg.conversation_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message types test failed: {e}")
        return False

def test_agents_structure():
    """Test agents structure without full initialization"""
    print("\nTesting agents structure...")
    
    try:
        # Test if we can import the agent classes
        from agents.guide_ai import GuideAI, ProjectPhase
        from agents.implement_ai import ImplementAI, ImplementationTask, ImplementationResult
        
        # Test ProjectPhase
        phase = ProjectPhase(
            name="Test Phase",
            description="Test description",
            key_activities=["activity1", "activity2"],
            success_criteria=["criteria1", "criteria2"],
            estimated_duration="1 week"
        )
        print(f"✅ ProjectPhase created: {phase.name}")
        
        # Test ImplementationTask
        task = ImplementationTask(
            id="test_task",
            name="Test Task",
            description="Test description",
            task_type="test"
        )
        print(f"✅ ImplementationTask created: {task.name}")
        
        # Test ImplementationResult
        result = ImplementationResult(
            task_id="test_task",
            success=True,
            output={"result": "success"}
        )
        print(f"✅ ImplementationResult created: {result.task_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agents structure test failed: {e}")
        return False

def test_orchestrator_structure():
    """Test orchestrator structure"""
    print("\nTesting orchestrator structure...")
    
    try:
        from agents.duo_ai_orchestrator import DuoAIOrchestrator, ConversationSession, ProjectMilestone
        
        # Test ConversationSession
        session = ConversationSession(
            session_id="test_session",
            topic="Test topic",
            phase="planning"
        )
        print(f"✅ ConversationSession created: {session.session_id}")
        
        # Test ProjectMilestone
        milestone = ProjectMilestone(
            id="test_milestone",
            name="Test Milestone",
            description="Test description",
            phase="planning",
            criteria=["criteria1", "criteria2"]
        )
        print(f"✅ ProjectMilestone created: {milestone.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator structure test failed: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from agents.guide_ai import GuideAI
        from agents.implement_ai import ImplementAI
        
        # Test GuideAI initialization (without async dependencies)
        guide_ai = GuideAI()
        print(f"✅ GuideAI instance created")
        print(f"   - Current phase: {guide_ai.current_phase}")
        print(f"   - Project phases: {len(guide_ai.project_phases)} phases")
        
        # Test ImplementAI initialization (without async dependencies)
        implement_ai = ImplementAI()
        print(f"✅ ImplementAI instance created")
        print(f"   - Capabilities: {len(implement_ai.capabilities)} capabilities")
        print(f"   - Execution strategies: {len(implement_ai.execution_strategies)} strategies")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Duo AI System - Component Tests")
    print("=" * 40)
    
    tests = [
        test_message_types,
        test_agents_structure,
        test_orchestrator_structure,
        lambda: asyncio.run(test_basic_functionality())
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Duo AI System components are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)