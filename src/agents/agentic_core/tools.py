"""
Tool Registry and Framework - Enables agents to use and select tools
"""
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import inspect


class AgenticTool(ABC):
    """Base class for agentic tools."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize tool.
        
        Args:
            name: Tool name
            description: Tool description for agent selection
        """
        self.name = name
        self.description = description
        self.usage_count = 0
        self.success_count = 0
        self.last_used = None
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Returns:
            Dictionary with execution result
        """
        pass
    
    def __call__(self, **kwargs) -> Dict[str, Any]:
        """Make tool callable."""
        self.usage_count += 1
        self.last_used = datetime.now()
        
        try:
            result = self.execute(**kwargs)
            self.success_count += 1
            return {
                'success': True,
                'result': result,
                'tool': self.name
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': self.name
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        return {
            'name': self.name,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'success_rate': self.success_count / self.usage_count if self.usage_count > 0 else 0,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }


class ToolRegistry:
    """Registry for managing and discovering tools."""
    
    def __init__(self):
        self.tools: Dict[str, AgenticTool] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register(self, tool: AgenticTool, category: str = "general"):
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            category: Tool category for organization
        """
        self.tools[tool.name] = tool
        
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(tool.name)
    
    def get_tool(self, name: str) -> Optional[AgenticTool]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: str) -> List[AgenticTool]:
        """Get all tools in a category."""
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_all_tools(self) -> List[AgenticTool]:
        """Get all registered tools."""
        return list(self.tools.values())
    
    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """Get descriptions of all tools for agent selection."""
        return [
            {
                'name': tool.name,
                'description': tool.description,
                'stats': tool.get_stats()
            }
            for tool in self.tools.values()
        ]
    
    def find_tools_for_task(self, task_description: str) -> List[AgenticTool]:
        """
        Find relevant tools for a task (simple keyword matching).
        In production, use semantic search.
        
        Args:
            task_description: Description of the task
            
        Returns:
            List of potentially relevant tools
        """
        keywords = task_description.lower().split()
        relevant_tools = []
        
        for tool in self.tools.values():
            tool_text = f"{tool.name} {tool.description}".lower()
            if any(keyword in tool_text for keyword in keywords):
                relevant_tools.append(tool)
        
        return relevant_tools


# Concrete tool implementations for data labeling

class OCRTool(AgenticTool):
    """Tool for extracting text from documents using OCR."""
    
    def __init__(self, deepseek_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        super().__init__(
            name="ocr_extractor",
            description="Extract text from PDF and document files using OCR. Use for text documents, scanned PDFs, and images with text."
        )
        self.deepseek_api_key = deepseek_api_key
        self.openai_api_key = openai_api_key
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Execute OCR extraction."""
        # Import here to avoid circular dependency
        from agents.agents.content_extractor_agent import ContentExtractorAgent
        
        extractor = ContentExtractorAgent(
            deepseek_api_key=self.deepseek_api_key,
            openai_api_key=self.openai_api_key
        )
        
        result = extractor.extract_text_document(file_path)
        return result


class VisionAnalysisTool(AgenticTool):
    """Tool for analyzing images visually."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        super().__init__(
            name="vision_analyzer",
            description="Analyze images visually to identify objects, scenes, and visual features. Use for photos, diagrams, charts, and visual content."
        )
        self.openai_api_key = openai_api_key
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Execute vision analysis."""
        from agents.agents.content_extractor_agent import ContentExtractorAgent
        
        extractor = ContentExtractorAgent(openai_api_key=self.openai_api_key)
        result = extractor.extract_image(file_path)
        return result


class AudioTranscriptionTool(AgenticTool):
    """Tool for transcribing audio files."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        super().__init__(
            name="audio_transcriber",
            description="Transcribe audio files to text using Whisper. Use for MP3, WAV, speech recordings, and video files with audio."
        )
        self.openai_api_key = openai_api_key
    
    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Execute audio transcription."""
        from agents.agents.content_extractor_agent import ContentExtractorAgent
        
        extractor = ContentExtractorAgent(openai_api_key=self.openai_api_key)
        result = extractor.extract_audio(file_path)
        return result


class CategoryClassificationTool(AgenticTool):
    """Tool for classifying content into categories."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        super().__init__(
            name="category_classifier",
            description="Classify content into appropriate categories based on text or visual features. Use after content extraction."
        )
        self.openai_api_key = openai_api_key
    
    def execute(self, modality: str, content: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute category classification."""
        from agents.agents.category_classifier_agent import CategoryClassifierAgent
        
        classifier = CategoryClassifierAgent(openai_api_key=self.openai_api_key)
        result = classifier.classify_category(modality, content)
        return result


class LabelGenerationTool(AgenticTool):
    """Tool for generating structured labels."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        super().__init__(
            name="label_generator",
            description="Generate structured labels (topics, entities, keywords, etc.) from content. Use after content extraction and categorization."
        )
        self.openai_api_key = openai_api_key
    
    def execute(self, modality: str, content: Dict[str, Any], category: str, **kwargs) -> Dict[str, Any]:
        """Execute label generation."""
        from agents.agents.label_generator_agent import LabelGeneratorAgent
        
        generator = LabelGeneratorAgent(openai_api_key=self.openai_api_key)
        result = generator.generate_labels(modality, content, category)
        return result


class QualityCheckTool(AgenticTool):
    """Tool for validating labeling quality."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        super().__init__(
            name="quality_validator",
            description="Validate the quality of labeling results and identify issues. Use to check completeness and accuracy."
        )
        self.openai_api_key = openai_api_key
    
    def execute(self, result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute quality validation."""
        from agents.agents.quality_check_agent import QualityCheckAgent
        
        checker = QualityCheckAgent(openai_api_key=self.openai_api_key)
        quality_result = checker.check_quality(result)
        return quality_result


def create_default_tool_registry(
    deepseek_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> ToolRegistry:
    """
    Create a tool registry with default tools for data labeling.
    
    Args:
        deepseek_api_key: DeepSeek API key
        openai_api_key: OpenAI API key
        
    Returns:
        Configured ToolRegistry
    """
    registry = ToolRegistry()
    
    # Register extraction tools
    registry.register(
        OCRTool(deepseek_api_key, openai_api_key),
        category="extraction"
    )
    registry.register(
        VisionAnalysisTool(openai_api_key),
        category="extraction"
    )
    registry.register(
        AudioTranscriptionTool(openai_api_key),
        category="extraction"
    )
    
    # Register analysis tools
    registry.register(
        CategoryClassificationTool(openai_api_key),
        category="analysis"
    )
    registry.register(
        LabelGenerationTool(openai_api_key),
        category="analysis"
    )
    
    # Register validation tools
    registry.register(
        QualityCheckTool(openai_api_key),
        category="validation"
    )
    
    return registry
