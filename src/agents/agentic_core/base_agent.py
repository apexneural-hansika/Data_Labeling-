"""
Base Autonomous Agent - Foundation for all agentic agents
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import json

from .memory import AgentMemory, SharedMemory
from .tools import ToolRegistry
from .message_bus import MessageBus


class AutonomousAgent(ABC):
    """
    Base class for autonomous agents with memory, tools, and communication.
    """
    
    def __init__(
        self,
        agent_id: str,
        role: str,
        memory: AgentMemory,
        shared_memory: SharedMemory,
        tool_registry: ToolRegistry,
        message_bus: MessageBus,
        llm_client: Any = None
    ):
        """
        Initialize autonomous agent.
        
        Args:
            agent_id: Unique agent identifier
            role: Agent's role/specialty
            memory: Agent's personal memory
            shared_memory: Shared memory accessible by all agents
            tool_registry: Registry of available tools
            message_bus: Communication bus
            llm_client: LLM client for decision-making
        """
        self.agent_id = agent_id
        self.role = role
        self.memory = memory
        self.shared_memory = shared_memory
        self.tool_registry = tool_registry
        self.message_bus = message_bus
        self.llm_client = llm_client
        
        self.status = "idle"
        self.current_task = None
        self.decision_history = []
    
    @abstractmethod
    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task autonomously.
        
        Args:
            task: Task dictionary
            
        Returns:
            Result dictionary
        """
        pass
    
    def make_decision(self, situation: str, options: List[str]) -> Dict[str, Any]:
        """
        Make an autonomous decision using LLM.
        
        Args:
            situation: Description of current situation
            options: Available options
            
        Returns:
            Decision with reasoning
        """
        if not self.llm_client:
            # Fallback to first option if no LLM
            return {
                'choice': options[0] if options else None,
                'reasoning': 'No LLM available, using default',
                'confidence': 0.5
            }
        
        # Get relevant context from memory
        recent_context = self.memory.get_recent_context(n=3)
        
        prompt = f"""
You are {self.agent_id}, a {self.role} agent.

Current situation: {situation}

Recent context: {json.dumps(recent_context, indent=2)}

Available options:
{chr(10).join(f"{i+1}. {opt}" for i, opt in enumerate(options))}

Analyze the situation and choose the best option. Explain your reasoning.
Return JSON: {{"choice": "option text", "reasoning": "explanation", "confidence": 0.0-1.0}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an autonomous {self.role} agent making decisions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                decision = json.loads(decision_text)
            except:
                # Extract from text if JSON parsing fails
                decision = {
                    'choice': options[0] if options else None,
                    'reasoning': decision_text,
                    'confidence': 0.7
                }
            
            # Record decision
            self.decision_history.append({
                'timestamp': datetime.now().isoformat(),
                'situation': situation,
                'decision': decision
            })
            
            return decision
            
        except Exception as e:
            # Use print as fallback if logger not available
            try:
                from utils.logger import get_agent_logger
                logger = get_agent_logger(self.agent_id)
                logger.error("Decision-making error", error=str(e))
            except:
                print(f"[{self.agent_id}] Decision-making error: {e}")
            return {
                'choice': options[0] if options else None,
                'reasoning': f'Error in decision-making: {e}',
                'confidence': 0.3
            }
    
    def select_tool(self, task_description: str) -> Optional[str]:
        """
        Autonomously select the best tool for a task.
        
        Args:
            task_description: Description of the task
            
        Returns:
            Tool name or None
        """
        available_tools = self.tool_registry.find_tools_for_task(task_description)
        
        if not available_tools:
            return None
        
        if len(available_tools) == 1:
            return available_tools[0].name
        
        # Use LLM to choose best tool
        tool_options = [
            f"{tool.name}: {tool.description}"
            for tool in available_tools
        ]
        
        decision = self.make_decision(
            situation=f"Need to: {task_description}",
            options=tool_options
        )
        
        # Extract tool name from choice
        chosen_tool_name = decision['choice'].split(':')[0].strip()
        return chosen_tool_name
    
    def communicate(
        self,
        to_agent: str,
        message_type: str,
        content: Any,
        priority: int = 0
    ) -> str:
        """
        Send a message to another agent.
        
        Args:
            to_agent: Recipient agent ID
            message_type: Type of message
            content: Message content
            priority: Message priority
            
        Returns:
            Message ID
        """
        return self.message_bus.send(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            priority=priority
        )
    
    def check_messages(self) -> List[Any]:
        """Check for new messages."""
        return self.message_bus.get_unread_messages(self.agent_id)
    
    def reflect(self, result: Dict[str, Any]):
        """
        Reflect on task execution and learn.
        
        Args:
            result: Task execution result
        """
        reflection = {
            'task': self.current_task,
            'result': result,
            'success': result.get('success', False),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in memory
        self.memory.add_to_short_term(reflection)
        
        # Share insights if significant
        if result.get('quality_score', 0) > 0.8:
            self.communicate(
                to_agent='broadcast',
                message_type='insight',
                content={
                    'agent': self.agent_id,
                    'insight': f"Successfully completed {self.current_task.get('type')} with high quality",
                    'approach': result.get('approach_used')
                }
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'status': self.status,
            'current_task': self.current_task,
            'decisions_made': len(self.decision_history),
            'messages_sent': len(self.message_bus.get_agent_messages(self.agent_id))
        }
