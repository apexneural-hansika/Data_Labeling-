"""
Agent Memory System - Provides short-term, long-term, and episodic memory
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib
from collections import deque


class AgentMemory:
    """Memory system for individual agents with short-term and working memory."""
    
    def __init__(self, max_short_term: int = 10):
        """
        Initialize agent memory.
        
        Args:
            max_short_term: Maximum items in short-term memory
        """
        self.short_term = deque(maxlen=max_short_term)
        self.working_memory = {}
        self.context = {}
    
    def remember(self, key: str, value: Any):
        """Store information in working memory."""
        self.working_memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
    
    def recall(self, key: str) -> Optional[Any]:
        """Retrieve information from working memory."""
        item = self.working_memory.get(key)
        return item['value'] if item else None
    
    def add_to_short_term(self, item: Dict[str, Any]):
        """Add item to short-term memory (FIFO queue)."""
        self.short_term.append({
            **item,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_recent_context(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get recent items from short-term memory."""
        return list(self.short_term)[-n:]
    
    def set_context(self, context: Dict[str, Any]):
        """Set current context for the agent."""
        self.context = context
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return self.context
    
    def clear_working_memory(self):
        """Clear working memory."""
        self.working_memory.clear()


class SharedMemory:
    """Shared memory accessible by all agents in the system."""
    
    def __init__(self):
        self.shared_state = {}
        self.agent_states = {}
        self.global_context = {}
    
    def set_shared(self, key: str, value: Any, agent_id: str):
        """Set shared state accessible by all agents."""
        self.shared_state[key] = {
            'value': value,
            'set_by': agent_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_shared(self, key: str) -> Optional[Any]:
        """Get shared state."""
        item = self.shared_state.get(key)
        return item['value'] if item else None
    
    def set_agent_state(self, agent_id: str, state: Dict[str, Any]):
        """Set state for a specific agent."""
        self.agent_states[agent_id] = {
            'state': state,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get state of a specific agent."""
        item = self.agent_states.get(agent_id)
        return item['state'] if item else None
    
    def get_all_agent_states(self) -> Dict[str, Any]:
        """Get states of all agents."""
        return {
            agent_id: data['state']
            for agent_id, data in self.agent_states.items()
        }
    
    def set_global_context(self, context: Dict[str, Any]):
        """Set global context for all agents."""
        self.global_context = context


class ExperienceDatabase:
    """
    Long-term memory storing past experiences for learning.
    In production, this would use a vector database like Chroma or Pinecone.
    """
    
    def __init__(self, storage_path: str = "experiences.json"):
        """
        Initialize experience database.
        
        Args:
            storage_path: Path to store experiences
        """
        self.storage_path = storage_path
        self.experiences = []
        self.load_experiences()
    
    def store_experience(self, experience: Dict[str, Any]):
        """
        Store a new experience.
        
        Args:
            experience: Dictionary containing task, action, result, quality
        """
        exp_id = self._generate_id(experience)
        
        experience_record = {
            'id': exp_id,
            'timestamp': datetime.now().isoformat(),
            **experience
        }
        
        self.experiences.append(experience_record)
        self.save_experiences()
    
    def recall_similar_experiences(
        self,
        query: Dict[str, Any],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past experiences.
        
        Args:
            query: Query parameters to match
            top_k: Number of top experiences to return
            
        Returns:
            List of similar experiences
        """
        # Simple similarity based on matching fields
        # In production, use vector similarity search
        scored_experiences = []
        
        for exp in self.experiences:
            score = self._calculate_similarity(query, exp)
            scored_experiences.append((score, exp))
        
        # Sort by score and return top_k
        scored_experiences.sort(key=lambda x: x[0], reverse=True)
        return [exp for _, exp in scored_experiences[:top_k]]
    
    def get_high_quality_experiences(
        self,
        min_quality: float = 0.8,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get high-quality past experiences for learning."""
        high_quality = [
            exp for exp in self.experiences
            if exp.get('quality_score', 0) >= min_quality
        ]
        return high_quality[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored experiences."""
        if not self.experiences:
            return {'total': 0}
        
        quality_scores = [
            exp.get('quality_score', 0)
            for exp in self.experiences
        ]
        
        return {
            'total': len(self.experiences),
            'avg_quality': sum(quality_scores) / len(quality_scores),
            'max_quality': max(quality_scores),
            'min_quality': min(quality_scores)
        }
    
    def _generate_id(self, experience: Dict[str, Any]) -> str:
        """Generate unique ID for experience."""
        content = json.dumps(experience, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _calculate_similarity(
        self,
        query: Dict[str, Any],
        experience: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between query and experience."""
        score = 0.0
        total_fields = 0
        
        for key in query:
            if key in experience:
                total_fields += 1
                if query[key] == experience[key]:
                    score += 1.0
                elif isinstance(query[key], str) and isinstance(experience[key], str):
                    # Simple string similarity
                    if query[key].lower() in experience[key].lower():
                        score += 0.5
        
        return score / total_fields if total_fields > 0 else 0.0
    
    def save_experiences(self):
        """Save experiences to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.experiences, f, indent=2)
        except Exception as e:
            print(f"Error saving experiences: {e}")
    
    def load_experiences(self):
        """Load experiences from disk."""
        try:
            with open(self.storage_path, 'r') as f:
                self.experiences = json.load(f)
        except FileNotFoundError:
            self.experiences = []
        except Exception as e:
            print(f"Error loading experiences: {e}")
            self.experiences = []
