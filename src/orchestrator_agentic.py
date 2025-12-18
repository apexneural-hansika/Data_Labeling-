"""
Agentic Orchestrator - True agentic system with autonomous agents
"""
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from config import Config

from agents.agentic_core.memory import AgentMemory, SharedMemory, ExperienceDatabase
from agents.agentic_core.tools import create_default_tool_registry
from agents.agentic_core.message_bus import MessageBus
from agents.agentic_agents.supervisor import SupervisorAgent
from agents.agentic_agents.autonomous_extractor import AutonomousContentExtractorAgent
from utils.logger import get_system_logger
from utils.learning_analyzer import LearningAnalyzer
from utils.database import EmbeddingDatabase
from utils.guardrails import Guardrails
from utils.cache import ResultCache

logger = get_system_logger()


class AgenticOrchestrator:
    """
    True agentic orchestrator with autonomous agents, memory, tools, and planning.
    """
    
    def __init__(
        self,
        deepseek_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize agentic orchestrator.
        
        Args:
            deepseek_api_key: DeepSeek API key (optional)
            openai_api_key: OpenAI API key (required)
        """
        logger.info("="*60)
        logger.info("INITIALIZING TRUE AGENTIC SYSTEM")
        logger.info("="*60)
        
        # Store API keys for later use
        self.openai_api_key = openai_api_key
        self.deepseek_api_key = deepseek_api_key
        
        # Initialize LLM client
        base_url = Config.get_base_url()
        self.llm_client = OpenAI(
            api_key=openai_api_key,
            base_url=base_url
        ) if base_url else OpenAI(api_key=openai_api_key)
        
        # Initialize core infrastructure
        logger.info("Initializing core infrastructure")
        self.shared_memory = SharedMemory()
        self.message_bus = MessageBus()
        self.tool_registry = create_default_tool_registry(
            deepseek_api_key=deepseek_api_key,
            openai_api_key=openai_api_key
        )
        self.experience_db = ExperienceDatabase()
        self.learning_analyzer = LearningAnalyzer(self.experience_db)
        
        # Initialize embedding database (optional, can be disabled via config)
        self.embedding_db = None
        if Config.ENABLE_EMBEDDING_STORAGE:
            try:
                # Use direct OpenAI key for embeddings (database module will handle OpenRouter keys)
                # The database module will auto-select HuggingFace if OpenAI key is not available
                embedding_key = Config.get_openai_key_for_embeddings()
                self.embedding_db = EmbeddingDatabase(
                    connection_string=Config.SUPABASE_DB_URL,
                    openai_api_key=embedding_key,
                    embedding_provider_type=Config.EMBEDDING_PROVIDER
                )
                logger.info("Embedding database initialized", provider=Config.EMBEDDING_PROVIDER)
            except Exception as e:
                logger.warning("Failed to initialize embedding database", error=str(e))
                logger.warning("Embedding storage will be disabled")
        
        # Initialize guardrails (optional, can be disabled via config)
        self.guardrails = None
        if Config.ENABLE_GUARDRAILS:
            try:
                self.guardrails = Guardrails()
                logger.info("Guardrails initialized",
                           content_filter=self.guardrails.enable_content_filter,
                           pii_detection=self.guardrails.enable_pii_detection)
            except Exception as e:
                logger.warning("Failed to initialize guardrails", error=str(e))
                logger.warning("Guardrails will be disabled")
        
        # Initialize result cache (optional, can be disabled via config)
        self.result_cache = None
        if Config.ENABLE_CACHING:
            try:
                self.result_cache = ResultCache(
                    embedding_db=self.embedding_db,
                    enable_memory_cache=Config.ENABLE_MEMORY_CACHE,
                    enable_db_cache=Config.ENABLE_DB_CACHE,
                    memory_cache_size=Config.MEMORY_CACHE_SIZE,
                    memory_cache_ttl=Config.MEMORY_CACHE_TTL
                )
                logger.info("Result cache initialized",
                           memory_cache=Config.ENABLE_MEMORY_CACHE,
                           db_cache=Config.ENABLE_DB_CACHE)
            except Exception as e:
                logger.warning("Failed to initialize result cache", error=str(e))
                logger.warning("Caching will be disabled")
        
        tool_count = len(self.tool_registry.get_all_tools())
        exp_count = self.experience_db.get_statistics()['total']
        logger.info("Core infrastructure initialized", tools=tool_count, experiences=exp_count)
        
        # Log learning insights if we have experiences
        if exp_count > 0:
            insights = self.learning_analyzer.get_learning_insights()
            logger.info("Learning insights", 
                       avg_quality=insights['performance']['avg_quality'],
                       success_rate=insights['performance']['success_rate'],
                       quality_trend=insights['performance']['quality_trend'])
        
        # Initialize agents
        logger.info("Initializing autonomous agents")
        self.agents = self._create_agents()
        
        logger.info("Autonomous agents created", agent_count=len(self.agents))
        
        # Initialize supervisor
        logger.info("Initializing supervisor agent")
        self.supervisor = self._create_supervisor()
        
        logger.info("="*60)
        logger.info("AGENTIC SYSTEM READY")
        logger.info("="*60)
    
    def _create_agents(self) -> Dict[str, Any]:
        """Create autonomous agents."""
        agents = {}
        
        # Content Extractor Agent
        agents['content_extractor'] = AutonomousContentExtractorAgent(
            memory=AgentMemory(),
            shared_memory=self.shared_memory,
            tool_registry=self.tool_registry,
            message_bus=self.message_bus,
            llm_client=self.llm_client
        )
        logger.info("Content Extractor Agent created", agent_type="autonomous", capabilities="tool-using")
        
        # More agents can be added here
        # agents['analyzer'] = AutonomousAnalyzerAgent(...)
        # agents['validator'] = AutonomousValidatorAgent(...)
        
        return agents
    
    def _create_supervisor(self) -> SupervisorAgent:
        """Create supervisor agent."""
        available_agents = {
            'content_extractor': 'Extracts content from files using appropriate tools (OCR, vision, audio)',
            'analyzer': 'Analyzes and categorizes content, generates labels',
            'validator': 'Validates quality and completeness of results'
        }
        
        supervisor = SupervisorAgent(
            memory=AgentMemory(),
            shared_memory=self.shared_memory,
            tool_registry=self.tool_registry,
            message_bus=self.message_bus,
            llm_client=self.llm_client,
            available_agents=available_agents
        )
        
        logger.info("Supervisor Agent created", capabilities="planning, coordination")
        
        return supervisor
    
    def process_file(self, file_path: str, output_dir: str = 'output') -> Dict[str, Any]:
        """
        Process a file using the agentic system.
        
        Args:
            file_path: Path to file to process
            output_dir: Output directory for results
            
        Returns:
            Processing result
        """
        logger.info("="*60)
        logger.info("PROCESSING FILE", filename=os.path.basename(file_path))
        logger.info("="*60)
        
        start_time = datetime.now()
        
        # Check cache before processing
        if self.result_cache:
            try:
                file_id = os.path.splitext(os.path.basename(file_path))[0]
                cached_result = self.result_cache.get_cached_result(file_path, file_id)
                
                if cached_result:
                    logger.info("="*60)
                    logger.info("CACHE HIT - Returning cached result", filename=os.path.basename(file_path))
                    logger.info("="*60)
                    
                    # Add cache metadata
                    cached_result['cache_hit'] = True
                    cached_result['cache_source'] = 'memory' if Config.ENABLE_MEMORY_CACHE else 'database'
                    
                    return cached_result
                else:
                    logger.info("Cache miss - Processing file", filename=os.path.basename(file_path))
            except Exception as e:
                logger.warning("Cache check failed, proceeding with processing", error=str(e))
        
        try:
            # Prepare task
            task = {
                'type': 'label_file',
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'output_dir': output_dir,
                'timestamp': start_time.isoformat()
            }
            
            # Store task in shared memory
            self.shared_memory.set_global_context(task)
            
            # Make experience database available to agents via shared memory
            self.shared_memory.set_shared('experience_db_instance', self.experience_db, 'orchestrator')
            
            # Supervisor creates plan and coordinates execution
            result = self.supervisor.process(task)
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Ensure quality_score is present in result
            if 'quality_score' not in result or result.get('quality_score', 0) == 0:
                logger.warning("Quality score missing, performing quality check")
                from agents.agents.quality_check_agent import QualityCheckAgent
                quality_checker = QualityCheckAgent(openai_api_key=self.openai_api_key)
                quality_result = quality_checker.check_quality(result)
                result['quality_score'] = quality_result.get('quality_score', 0.0)
                result['quality_status'] = quality_result.get('quality_status', 'unknown')
                result['quality_check'] = quality_result
                logger.info("Quality check performed", quality_score=result['quality_score'])
            
            # Ensure quality_check structure exists
            if 'quality_check' not in result:
                result['quality_check'] = {
                    'quality_score': result.get('quality_score', 0.0),
                    'quality_status': result.get('quality_status', 'unknown'),
                    'issues': [],
                    'passed': result.get('quality_score', 0) >= 0.6
                }
            
            # Add metadata
            result['processing_time'] = processing_time
            result['timestamp'] = end_time.isoformat()
            result['agentic_system'] = True
            result['agents_involved'] = list(self.agents.keys()) + ['supervisor']
            
            # Ensure quality_score is at top level for easy access
            if 'quality_score' not in result:
                result['quality_score'] = result.get('quality_check', {}).get('quality_score', 0.0)
            
            # Apply guardrails validation
            if self.guardrails:
                try:
                    is_valid, violations, sanitized_result = self.guardrails.validate_output(result)
                    
                    if not is_valid:
                        logger.warning("Guardrail violations detected",
                                     violations=violations,
                                     violation_count=len(violations))
                        result = sanitized_result
                        result['guardrail_passed'] = False
                    else:
                        result['guardrail_passed'] = True
                        logger.info("Guardrails validation passed")
                except Exception as e:
                    logger.error("Guardrails validation error", error=str(e))
                    # Continue without guardrails if validation fails
                    result['guardrail_passed'] = None
                    result['guardrail_error'] = str(e)
            else:
                result['guardrail_passed'] = None
            
            # Store result in cache (after successful processing)
            if self.result_cache and result.get('success', False):
                try:
                    file_id = result.get('file_id') or os.path.splitext(os.path.basename(file_path))[0]
                    # Make a copy to avoid modifying original
                    result_copy = result.copy()
                    self.result_cache.store_result(file_path, result_copy, file_id)
                    logger.debug("Result stored in cache", file_path=file_path)
                except Exception as e:
                    logger.warning("Failed to store result in cache", error=str(e))
            
            # Store experience for learning (with more context for better similarity matching)
            experience_data = {
                'task': task,
                'result': result,
                'quality_score': result.get('quality_score', 0),
                'processing_time': processing_time,
                'success': result.get('success', False),
                'modality': result.get('modality', ''),
                'category': result.get('category', ''),
                'extraction_method': result.get('extraction_method', ''),
                'file_extension': os.path.splitext(file_path)[1].lower() if file_path else ''
            }
            self.experience_db.store_experience(experience_data)
            logger.info("Experience stored for learning", 
                       quality_score=experience_data['quality_score'],
                       modality=experience_data.get('modality'),
                       total_experiences=len(self.experience_db.experiences))
            
            # Save output
            if result.get('success', False):
                self._save_output(result, output_dir)
                
                # Store embedding in database
                if self.embedding_db:
                    try:
                        # Generate unique file_id from file_path or use existing identifier
                        file_id = result.get('file_id') or os.path.splitext(
                            os.path.basename(file_path)
                        )[0] if file_path else str(uuid.uuid4())
                        
                        # Store embedding
                        embedding_stored = self.embedding_db.store_embedding(
                            file_id=file_id,
                            file_name=result.get('file_name', os.path.basename(file_path) if file_path else 'unknown'),
                            output_data=result,
                            file_path=file_path
                        )
                        
                        if embedding_stored:
                            logger.info("Output stored as embedding in database", file_id=file_id)
                        else:
                            logger.warning("Failed to store embedding in database", file_id=file_id)
                    except Exception as e:
                        logger.error("Error storing embedding", error=str(e))
                        # Don't fail the whole process if embedding storage fails
            
            # Log statistics
            self._log_statistics(processing_time)
            
            logger.info("="*60)
            logger.info("PROCESSING COMPLETE", processing_time=processing_time)
            logger.info("="*60)
            
            return result
            
        except Exception as e:
            logger.exception("File processing error", file_path=file_path, error=str(e))
            return {
                'error': str(e),
                'file_name': os.path.basename(file_path),
                'success': False
            }
    
    def _save_output(self, result: Dict[str, Any], output_dir: str):
        """Save processing output."""
        from agents.agents.json_output_agent import JSONOutputAgent
        
        os.makedirs(output_dir, exist_ok=True)
        
        output_agent = JSONOutputAgent()
        output_file = os.path.join(
            output_dir,
            f"{result.get('file_name', 'output')}_agentic_labeled.json"
        )
        
        output_agent.save_json(result, output_file)
        logger.info("Output saved", output_file=output_file)
    
    def _log_statistics(self, processing_time: float):
        """Log system statistics."""
        logger.info("-"*60)
        logger.info("SYSTEM STATISTICS")
        logger.info("-"*60)
        
        # Message bus stats
        msg_stats = self.message_bus.get_statistics()
        logger.info("Message bus statistics", 
                   total_messages=msg_stats['total_messages'],
                   messages_by_type=msg_stats['messages_by_type'])
        
        # Tool usage stats
        tool_stats = {}
        for tool in self.tool_registry.get_all_tools():
            stats = tool.get_stats()
            if stats['usage_count'] > 0:
                tool_stats[stats['name']] = {
                    'usage_count': stats['usage_count'],
                    'success_rate': stats['success_rate']
                }
        if tool_stats:
            logger.info("Tool usage statistics", tools=tool_stats)
        
        # Experience database stats
        exp_stats = self.experience_db.get_statistics()
        logger.info("Experience database statistics",
                   total_experiences=exp_stats['total'],
                   avg_quality=exp_stats.get('avg_quality', 0))
        
        # Agent stats
        agent_stats = {}
        for agent_id, agent in self.agents.items():
            status = agent.get_status()
            agent_stats[agent_id] = {
                'decisions_made': status['decisions_made']
            }
        logger.info("Agent statistics", agents=agent_stats)
        
        logger.info("Processing time", seconds=processing_time)
        logger.info("-"*60)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            'agents': {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            },
            'supervisor': self.supervisor.get_status(),
            'message_bus': self.message_bus.get_statistics(),
            'experience_db': self.experience_db.get_statistics(),
            'tools': [
                tool.get_stats()
                for tool in self.tool_registry.get_all_tools()
            ]
        }
