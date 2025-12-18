"""
Message Bus - Enables agent-to-agent communication
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import defaultdict
from queue import Queue
import uuid


class AgentMessage:
    """Message sent between agents."""
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Any,
        priority: int = 0
    ):
        """
        Initialize agent message.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID (or 'broadcast' for all)
            message_type: Type of message (request, response, notification, etc.)
            content: Message content
            priority: Message priority (higher = more urgent)
        """
        self.id = str(uuid.uuid4())[:8]
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.timestamp = datetime.now()
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'from': self.from_agent,
            'to': self.to_agent,
            'type': self.message_type,
            'content': self.content,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat(),
            'read': self.read
        }


class MessageBus:
    """Central message bus for agent communication."""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.agent_queues: Dict[str, Queue] = defaultdict(Queue)
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_history: List[AgentMessage] = []
    
    def send(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Any,
        priority: int = 0
    ) -> str:
        """
        Send a message from one agent to another.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            message_type: Type of message
            content: Message content
            priority: Message priority
            
        Returns:
            Message ID
        """
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        self.messages.append(message)
        self.message_history.append(message)
        
        # Add to recipient's queue
        if to_agent != 'broadcast':
            self.agent_queues[to_agent].put(message)
        else:
            # Broadcast to all agents
            for agent_id in self.agent_queues.keys():
                if agent_id != from_agent:
                    self.agent_queues[agent_id].put(message)
        
        # Notify subscribers
        self._notify_subscribers(message)
        
        return message.id
    
    def receive(self, agent_id: str, block: bool = False, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        Receive a message for an agent.
        
        Args:
            agent_id: Agent ID
            block: Whether to block waiting for message
            timeout: Timeout in seconds
            
        Returns:
            AgentMessage or None
        """
        try:
            message = self.agent_queues[agent_id].get(block=block, timeout=timeout)
            message.read = True
            return message
        except:
            return None
    
    def get_unread_messages(self, agent_id: str) -> List[AgentMessage]:
        """Get all unread messages for an agent."""
        unread = []
        while not self.agent_queues[agent_id].empty():
            message = self.agent_queues[agent_id].get()
            message.read = True
            unread.append(message)
        return unread
    
    def broadcast(
        self,
        from_agent: str,
        message_type: str,
        content: Any
    ) -> str:
        """
        Broadcast a message to all agents.
        
        Args:
            from_agent: Sender agent ID
            message_type: Type of message
            content: Message content
            
        Returns:
            Message ID
        """
        return self.send(
            from_agent=from_agent,
            to_agent='broadcast',
            message_type=message_type,
            content=content
        )
    
    def subscribe(self, message_type: str, callback: Callable):
        """
        Subscribe to messages of a specific type.
        
        Args:
            message_type: Type of message to subscribe to
            callback: Function to call when message is received
        """
        self.subscribers[message_type].append(callback)
    
    def _notify_subscribers(self, message: AgentMessage):
        """Notify subscribers of a new message."""
        for callback in self.subscribers.get(message.message_type, []):
            try:
                callback(message)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")
    
    def get_conversation(self, agent1: str, agent2: str) -> List[AgentMessage]:
        """Get conversation history between two agents."""
        return [
            msg for msg in self.message_history
            if (msg.from_agent == agent1 and msg.to_agent == agent2) or
               (msg.from_agent == agent2 and msg.to_agent == agent1)
        ]
    
    def get_agent_messages(self, agent_id: str) -> List[AgentMessage]:
        """Get all messages sent or received by an agent."""
        return [
            msg for msg in self.message_history
            if msg.from_agent == agent_id or msg.to_agent == agent_id
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        total_messages = len(self.message_history)
        
        messages_by_type = defaultdict(int)
        messages_by_agent = defaultdict(int)
        
        for msg in self.message_history:
            messages_by_type[msg.message_type] += 1
            messages_by_agent[msg.from_agent] += 1
        
        return {
            'total_messages': total_messages,
            'messages_by_type': dict(messages_by_type),
            'messages_by_agent': dict(messages_by_agent),
            'active_agents': len(self.agent_queues)
        }
    
    def clear_history(self):
        """Clear message history (keep queues)."""
        self.message_history.clear()
