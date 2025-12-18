"""
Autonomous Content Extractor Agent - Tool-using agent with decision-making
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import os

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.agentic_core.base_agent import AutonomousAgent
from agents.agentic_core.memory import AgentMemory, SharedMemory
from agents.agentic_core.tools import ToolRegistry
from agents.agentic_core.message_bus import MessageBus
from utils.logger import get_agent_logger


class AutonomousContentExtractorAgent(AutonomousAgent):
    """
    Autonomous agent that extracts content by selecting and using appropriate tools.
    """
    
    def __init__(
        self,
        memory: AgentMemory,
        shared_memory: SharedMemory,
        tool_registry: ToolRegistry,
        message_bus: MessageBus,
        llm_client: Any = None
    ):
        super().__init__(
            agent_id="content_extractor",
            role="content extraction specialist",
            memory=memory,
            shared_memory=shared_memory,
            tool_registry=tool_registry,
            message_bus=message_bus,
            llm_client=llm_client
        )
        self.logger = get_agent_logger(self.agent_id)
    
    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Autonomously extract content from a file.
        
        Args:
            task: Task containing file_path and modality
            
        Returns:
            Extraction result
        """
        self.status = "processing"
        self.current_task = task
        
        file_path = task['file_path']
        modality = task.get('modality', 'unknown')
        
        self.logger.info("Processing file", file_path=file_path, modality=modality)
        
        # Check if we've seen similar files before and learn from them
        experience_db = self.shared_memory.get_shared('experience_db_instance')
        similar_experiences = []
        
        if experience_db:
            # Query for similar experiences
            query = {
                'modality': modality,
                'file_name': os.path.basename(file_path)
            }
            similar_experiences = experience_db.recall_similar_experiences(query, top_k=2)
            
            if similar_experiences:
                self.logger.info("Found similar past cases", count=len(similar_experiences))
                # Store in shared memory for strategy decision
                self.shared_memory.set_shared('similar_experiences', similar_experiences, self.agent_id)
        
        # Decide on extraction strategy (will use experiences if available)
        strategy = self._choose_extraction_strategy(file_path, modality, similar_experiences)
        self.logger.info("Extraction strategy chosen", strategy=strategy['choice'], reasoning=strategy.get('reasoning', ''))
        
        # Select and use appropriate tool
        tool_name = self.select_tool(strategy['choice'])
        
        if not tool_name:
            self.logger.error("No suitable tool found", strategy=strategy['choice'])
            return {
                'success': False,
                'error': 'No suitable tool found',
                'agent': self.agent_id
            }
        
        self.logger.info("Using tool", tool_name=tool_name)
        
        # Execute tool
        tool = self.tool_registry.get_tool(tool_name)
        result = tool(file_path=file_path)
        
        # Reflect on result
        self.reflect(result)
        
        # Store in memory
        self.memory.remember('last_extraction', result)
        
        self.status = "idle"
        return result
    
    def _choose_extraction_strategy(
        self,
        file_path: str,
        modality: str,
        similar_experiences: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Autonomously choose extraction strategy.
        
        Args:
            file_path: Path to file
            modality: File modality
            
        Returns:
            Strategy decision
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Learn from past experiences
        experience_context = ""
        if similar_experiences:
            experience_context = "\n\nLEARN FROM PAST EXPERIENCES:\n"
            for exp in similar_experiences[:2]:
                exp_result = exp.get('result', {})
                quality = exp.get('quality_score', 0)
                success = exp.get('success', False)
                extraction_method = exp_result.get('extraction_method', 'unknown')
                
                experience_context += f"""
- Past similar file: Quality={quality:.2f}, Success={success}, Method={extraction_method}
"""
        
        situation = f"""
File: {os.path.basename(file_path)}
Extension: {file_ext}
Modality: {modality}
Size: {file_size} bytes
{experience_context}
"""
        
        # Define strategy options based on modality
        if modality == 'text_document':
            options = [
                "Use OCR extraction for text documents",
                "Use vision analysis if document is primarily visual"
            ]
        elif modality == 'image':
            options = [
                "Use vision analysis for visual content",
                "Use OCR if image contains significant text"
            ]
        elif modality == 'audio':
            options = [
                "Use audio transcription with Whisper"
            ]
        else:
            options = [
                "Analyze file and determine best extraction method"
            ]
        
        # If we have successful past experiences, prioritize those methods
        if similar_experiences:
            successful_methods = [
                exp.get('result', {}).get('extraction_method')
                for exp in similar_experiences
                if exp.get('success', False) and exp.get('quality_score', 0) > 0.6
            ]
            if successful_methods:
                # Add learned method as first option
                learned_method = successful_methods[0]
                if learned_method == 'ocr':
                    options.insert(0, f"Use OCR extraction (learned: worked well for similar files)")
                elif learned_method == 'vision':
                    options.insert(0, f"Use vision analysis (learned: worked well for similar files)")
        
        return self.make_decision(situation, options)
