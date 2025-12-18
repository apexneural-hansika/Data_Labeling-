"""
Supervisor Agent - Plans and coordinates other agents
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.agentic_core.base_agent import AutonomousAgent
from agents.agentic_core.memory import AgentMemory, SharedMemory
from agents.agentic_core.tools import ToolRegistry
from agents.agentic_core.message_bus import MessageBus
from utils.logger import get_agent_logger


class SupervisorAgent(AutonomousAgent):
    """
    Supervisor agent that creates plans and coordinates other agents.
    """
    
    def __init__(
        self,
        memory: AgentMemory,
        shared_memory: SharedMemory,
        tool_registry: ToolRegistry,
        message_bus: MessageBus,
        llm_client: Any,
        available_agents: Dict[str, str]
    ):
        super().__init__(
            agent_id="supervisor",
            role="planning and coordination specialist",
            memory=memory,
            shared_memory=shared_memory,
            tool_registry=tool_registry,
            message_bus=message_bus,
            llm_client=llm_client
        )
        self.available_agents = available_agents  # {agent_id: description}
        self.logger = get_agent_logger(self.agent_id)
    
    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and execute a plan for the task.
        
        Args:
            task: Task to accomplish
            
        Returns:
            Execution result
        """
        self.status = "planning"
        self.current_task = task
        
        self.logger.info("=== PLANNING PHASE ===")
        
        # Create plan
        plan = self.create_plan(task)
        
        self.logger.info("Plan created", step_count=len(plan['steps']), reasoning=plan.get('reasoning', ''))
        
        # Store plan in shared memory
        self.shared_memory.set_shared('current_plan', plan, self.agent_id)
        
        # Execute plan
        self.status = "coordinating"
        self.logger.info("=== EXECUTION PHASE ===")
        
        result = self.execute_plan(plan, task)
        
        self.status = "idle"
        return result
    
    def create_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a dynamic plan for the task.
        
        Args:
            task: Task dictionary
            
        Returns:
            Plan with steps and reasoning
        """
        # Analyze task
        task_description = json.dumps(task, indent=2)
        
        # Get available agents and tools
        agents_desc = "\n".join([
            f"- {agent_id}: {desc}"
            for agent_id, desc in self.available_agents.items()
        ])
        
        tools_desc = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tool_registry.get_tool_descriptions()
        ])
        
        # Check for similar past experiences
        recent_context = self.memory.get_recent_context(n=3)
        
        # Retrieve similar past experiences from experience database
        experience_db = self.shared_memory.get_shared('experience_db_instance')
        similar_experiences = []
        experience_insights = ""
        
        if experience_db:
            # Query for similar experiences based on task characteristics
            query = {
                'type': task.get('type', 'label_file'),
                'modality': task.get('modality', '')
            }
            similar_experiences = experience_db.recall_similar_experiences(query, top_k=3)
            
            if similar_experiences:
                self.logger.info("Found similar past experiences", count=len(similar_experiences))
                # Get high-quality experiences for learning
                high_quality = experience_db.get_high_quality_experiences(min_quality=0.7, limit=2)
                
                # Build experience insights
                if similar_experiences:
                    experience_insights = "\n\nPAST EXPERIENCES (Learn from these):\n"
                    for i, exp in enumerate(similar_experiences[:2], 1):
                        exp_result = exp.get('result', {})
                        quality = exp.get('quality_score', 0)
                        success = exp.get('success', False)
                        exp_modality = exp_result.get('modality', 'unknown')
                        exp_category = exp_result.get('category', 'unknown')
                        
                        experience_insights += f"""
Experience {i}:
  - Modality: {exp_modality}
  - Category: {exp_category}
  - Quality Score: {quality:.2f}
  - Success: {success}
  - Processing Time: {exp.get('processing_time', 0):.1f}s
"""
                
                if high_quality:
                    experience_insights += "\nHIGH-QUALITY EXAMPLES:\n"
                    for exp in high_quality[:2]:
                        quality = exp.get('quality_score', 0)
                        experience_insights += f"  - Quality: {quality:.2f}, Category: {exp.get('result', {}).get('category', 'N/A')}\n"
        
        planning_prompt = f"""
You are a supervisor agent creating an execution plan.

TASK:
{task_description}

AVAILABLE AGENTS:
{agents_desc}

AVAILABLE TOOLS:
{tools_desc}

RECENT CONTEXT:
{json.dumps(recent_context, indent=2)}
{experience_insights}

Create an optimal execution plan. Consider:
1. Can we skip any steps based on obvious information?
2. What's the most efficient order of operations?
3. Should we do quality checks mid-process?
4. Are there any risks or special considerations?
5. What worked well in similar past experiences? (Use the PAST EXPERIENCES above)
6. What should we avoid based on past failures?

Return a JSON plan with this structure:
{{
    "steps": [
        {{
            "step_number": 1,
            "agent": "agent_id",
            "action": "action description",
            "reasoning": "why this step is needed",
            "parameters": {{}},
            "expected_output": "what we expect"
        }}
    ],
    "reasoning": "overall plan reasoning",
    "estimated_time": "time estimate",
    "risk_factors": ["potential risks"]
}}

Be smart and efficient. Skip unnecessary steps.
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert planning agent. Create efficient, adaptive plans."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.3
            )
            
            plan_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(plan_text)
            
            # Store in decision history
            self.decision_history.append({
                'type': 'plan_creation',
                'task': task,
                'plan': plan,
                'timestamp': datetime.now().isoformat()
            })
            
            return plan
            
        except Exception as e:
            self.logger.exception("Planning error", error=str(e))
            # Fallback to simple plan
            return self._create_fallback_plan(task)
    
    def execute_plan(self, plan: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plan by coordinating agents.
        
        Args:
            plan: Execution plan
            task: Original task
            
        Returns:
            Execution result
        """
        state = {'file_path': task['file_path']}
        
        for step in plan['steps']:
            step_num = step['step_number']
            agent_id = step['agent']
            action = step['action']
            reasoning = step['reasoning']
            
            self.logger.info("Executing step", step_number=step_num, action=action, agent=agent_id, reasoning=reasoning)
            
            # Delegate to agent via message bus
            self.communicate(
                to_agent=agent_id,
                message_type='task_request',
                content={
                    'action': action,
                    'parameters': step.get('parameters', {}),
                    'state': state
                },
                priority=1
            )
            
            # In a real implementation, wait for agent response
            # For now, we'll execute directly
            result = self._execute_step(step, state)
            
            # Check if step was successful
            if not result.get('success', False):
                self.logger.warning("Step failed", step_number=step_num, error=result.get('error'))
                
                # Decide whether to replan or continue
                should_replan = self._should_replan(step, result)
                
                if should_replan:
                    self.logger.info("Replanning due to failure")
                    new_plan = self.create_plan({**task, 'previous_failure': result})
                    return self.execute_plan(new_plan, task)
                else:
                    self.logger.warning("Continuing despite failure")
            
            # Update state with result
            state.update(result)
            
            # Store step result in memory
            self.memory.add_to_short_term({
                'step': step_num,
                'result': result,
                'success': result.get('success', False)
            })
        
        # Ensure categorization is always performed if not already done
        category = state.get('category', '').strip()
        if not category or category.lower() in ['uncategorized', 'unknown', 'none', 'null']:
            modality = state.get('modality', 'unknown')
            has_content = False
            
            if modality == 'image':
                has_content = bool(state.get('visual_features', '').strip())
            elif modality in ['text_document', 'audio']:
                has_content = bool(state.get('raw_text', '').strip())
            
            if has_content:
                self.logger.info("Category not assigned, performing categorization now", modality=modality)
                tool = self.tool_registry.get_tool('category_classifier')
                if tool:
                    try:
                        result = tool(modality=modality, content=state)
                        if result.get('success'):
                            category_data = result.get('result', {})
                            state['category'] = category_data.get('category', 'uncategorized')
                            state['confidence'] = category_data.get('confidence', 0.0)
                            state['category_reasoning'] = category_data.get('reasoning', '')
                            self.logger.info("Category assigned", category=state['category'], confidence=state['confidence'])
                        else:
                            self.logger.warning("Categorization failed", error=result.get('error'))
                            state['category'] = 'uncategorized'
                    except Exception as e:
                        self.logger.error("Categorization error", error=str(e))
                        state['category'] = 'uncategorized'
            else:
                self.logger.warning("Cannot categorize - no content available", modality=modality)
                state['category'] = 'uncategorized'
        
        # Ensure quality check is always performed if not already done
        if 'quality_score' not in state or state.get('quality_score', 0) == 0:
            self.logger.info("Quality check not in plan, performing quality check now")
            tool = self.tool_registry.get_tool('quality_validator')
            if tool:
                quality_result = tool(result=state)
                if quality_result.get('success'):
                    quality_data = quality_result.get('result', {})
                    state['quality_score'] = quality_data.get('quality_score', 0.0)
                    state['quality_status'] = quality_data.get('quality_status', 'unknown')
                    state['quality_check'] = quality_data
                    self.logger.info("Quality check completed", quality_score=state['quality_score'])
        
        # Ensure quality_check structure is present
        if 'quality_check' not in state:
            # Create a default quality check structure
            state['quality_check'] = {
                'quality_score': state.get('quality_score', 0.0),
                'quality_status': state.get('quality_status', 'unknown'),
                'issues': [],
                'passed': False
            }
        
        # Ensure quality_score is at top level
        if 'quality_score' not in state:
            state['quality_score'] = state.get('quality_check', {}).get('quality_score', 0.0)
        
        # Mark as successful if we have results
        if 'success' not in state:
            state['success'] = True
        
        self.logger.info("=== PLAN COMPLETED ===", quality_score=state.get('quality_score', 0))
        return state
    
    def _execute_step(self, step: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single plan step."""
        agent_id = step['agent']
        action = step['action']
        
        # Determine modality if not already set
        if 'modality' not in state:
            file_path = state.get('file_path', '')
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.pdf', '.txt', '.docx', '.doc', '.csv']:
                state['modality'] = 'text_document'
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                state['modality'] = 'image'
            elif ext in ['.mp3', '.wav', '.flac', '.m4a', '.mp4']:
                state['modality'] = 'audio'
            else:
                state['modality'] = 'unknown'
        
        # Map actions to tool executions
        # Use more precise matching to avoid false positives
        action_lower = action.lower().strip()
        
        # Check if action starts with "use [tool_name]" pattern
        # Extract tool name if present
        tool_name_from_action = None
        if action_lower.startswith('use '):
            # Extract tool name: "use category_classifier to..." -> "category_classifier"
            parts = action_lower.split()
            if len(parts) >= 2:
                tool_name_from_action = parts[1]
        
        # Check for extraction actions (must start with extract/use ocr/use vision/transcribe)
        is_extraction = (
            action_lower.startswith('extract') or
            action_lower.startswith('use ocr') or
            action_lower.startswith('use vision') or
            action_lower.startswith('transcribe') or
            action_lower.startswith('analyze image') or
            action_lower.startswith('get visual') or
            tool_name_from_action in ['ocr_extractor', 'vision_analyzer', 'audio_transcriber']
        )
        
        # Check for classification actions
        is_classification = (
            action_lower.startswith('classify') or
            action_lower.startswith('categorize') or
            action_lower.startswith('assign category') or
            action_lower.startswith('determine category') or
            action_lower.startswith('analyze and categorize') or
            'analyze.*categorize' in action_lower or
            tool_name_from_action == 'category_classifier'
        )
        
        # Check for labeling actions
        is_labeling = (
            action_lower.startswith('generate label') or
            action_lower.startswith('generate structured') or
            action_lower.startswith('create label') or
            action_lower.startswith('label') or
            action_lower.startswith('identify') or
            action_lower.startswith('analyze the extracted') or
            action_lower.startswith('analyze and generate') or
            'generate.*label' in action_lower or
            'analyze.*label' in action_lower or
            tool_name_from_action == 'label_generator'
        )
        
        # Check for quality/validation actions
        is_validation = (
            action_lower.startswith('validate') or
            action_lower.startswith('check quality') or
            action_lower.startswith('verify') or
            action_lower.startswith('quality check') or
            tool_name_from_action == 'quality_validator'
        )
        
        if is_extraction:
            modality = state.get('modality', 'unknown')
            
            # Select appropriate extraction tool
            if modality == 'text_document':
                tool = self.tool_registry.get_tool('ocr_extractor')
            elif modality == 'image':
                tool = self.tool_registry.get_tool('vision_analyzer')
            elif modality == 'audio':
                tool = self.tool_registry.get_tool('audio_transcriber')
            else:
                return {'success': False, 'error': f'Unknown modality: {modality}'}
            
            if tool:
                result = tool(file_path=state['file_path'])
                self.logger.info("Extraction completed", success=result.get('success'), result_keys=list(result.get('result', {}).keys()))
                
                if result.get('success'):
                    # Merge extraction result into state - preserve ALL fields
                    extraction_data = result.get('result', {})
                    state['raw_text'] = extraction_data.get('raw_text', '')
                    state['visual_features'] = extraction_data.get('visual_features', '')
                    state['extraction_method'] = extraction_data.get('extraction_method', '')
                    state['file_name'] = os.path.basename(state['file_path'])
                    
                    # Debug logging
                    if modality == 'image':
                        self.logger.debug("Image extraction", visual_features_length=len(state.get('visual_features', '')))
                    elif modality == 'text_document':
                        self.logger.debug("Text extraction", raw_text_length=len(state.get('raw_text', '')))
                    elif modality == 'audio':
                        self.logger.debug("Audio extraction", raw_text_length=len(state.get('raw_text', '')))
                
                return result
        
        elif is_classification:
            tool = self.tool_registry.get_tool('category_classifier')
            if tool:
                # Ensure we have content to classify
                modality = state.get('modality', 'unknown')
                has_content = False
                
                if modality == 'image':
                    has_content = bool(state.get('visual_features', '').strip())
                    self.logger.debug("Classifying image", has_visual_features=has_content)
                else:
                    has_content = bool(state.get('raw_text', '').strip())
                    self.logger.debug("Classifying content", modality=modality, has_raw_text=has_content)
                
                if not has_content:
                    self.logger.warning("No content available for classification", modality=modality)
                    return {
                        'success': False,
                        'error': f'No content extracted for {modality} classification'
                    }
                
                result = tool(
                    modality=modality,
                    content=state  # Pass entire state
                )
                
                if result.get('success'):
                    # Extract category from result
                    category_data = result.get('result', {})
                    state['category'] = category_data.get('category', 'uncategorized')
                    state['confidence'] = category_data.get('confidence', 0.0)
                    state['category_reasoning'] = category_data.get('reasoning', '')
                    self.logger.info("Category assigned", category=state['category'], confidence=state['confidence'])
                
                return result
        
        elif is_labeling:
            tool = self.tool_registry.get_tool('label_generator')
            if tool:
                result = tool(
                    modality=state.get('modality', 'unknown'),
                    content=state,
                    category=state.get('category', 'uncategorized')
                )
                if result.get('success'):
                    # Extract labels from result
                    label_data = result.get('result', {})
                    state['labels'] = label_data.get('labels', {})
                    state['label_confidence'] = label_data.get('confidence', 0.0)
                return result
        
        elif is_validation:
            tool = self.tool_registry.get_tool('quality_validator')
            if tool:
                result = tool(result=state)
                if result.get('success'):
                    # Extract quality metrics
                    quality_data = result.get('result', {})
                    state['quality_score'] = quality_data.get('quality_score', 0.0)
                    state['quality_status'] = quality_data.get('quality_status', 'unknown')
                    state['quality_check'] = quality_data
                return result
        
        # If no match, return success with note
        self.logger.warning("No tool matched for action", action=action)
        return {'success': True, 'note': f'No tool matched for action: {action}'}
    
    def _should_replan(self, failed_step: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Decide whether to replan after a failure."""
        # Use LLM to decide
        decision = self.make_decision(
            situation=f"Step failed: {failed_step['action']}. Error: {result.get('error')}",
            options=[
                "Replan with alternative approach",
                "Continue with current plan",
                "Abort and report error"
            ]
        )
        
        return 'replan' in decision['choice'].lower()
    
    def _create_fallback_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback plan."""
        return {
            "steps": [
                {
                    "step_number": 1,
                    "agent": "content_extractor",
                    "action": "Extract content from file",
                    "reasoning": "Need to extract content first",
                    "parameters": {},
                    "expected_output": "Extracted content"
                },
                {
                    "step_number": 2,
                    "agent": "analyzer",
                    "action": "Classify category",
                    "reasoning": "Categorize extracted content",
                    "parameters": {},
                    "expected_output": "Category assignment"
                },
                {
                    "step_number": 3,
                    "agent": "analyzer",
                    "action": "Generate labels",
                    "reasoning": "Create structured labels",
                    "parameters": {},
                    "expected_output": "Structured labels"
                },
                {
                    "step_number": 4,
                    "agent": "validator",
                    "action": "Validate quality",
                    "reasoning": "Ensure quality standards",
                    "parameters": {},
                    "expected_output": "Quality report"
                }
            ],
            "reasoning": "Standard labeling pipeline (fallback plan)",
            "estimated_time": "2-5 minutes",
            "risk_factors": ["API failures", "Low quality content"]
        }
