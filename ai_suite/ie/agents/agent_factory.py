from typing import Type, Dict, Any
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker

class AgentFactory:
    def __init__(
        self,
        llm: LLMFactory,
        model_name: str,
        output_dir: str,
        token_tracker: TokenUsageTracker,
        logger = None
    ):
        self.llm = llm
        self.model_name = model_name
        self.output_dir = output_dir
        self.token_tracker = token_tracker
        self.logger = logger
        
    def create_agent(
        self, 
        agent_class: Type[BaseAgent], 
        **kwargs
    ) -> BaseAgent:
        """Create an agent with common configuration"""
        base_config = {
            "llm_client": self.llm,
            "model_name": self.model_name,
            "token_tracker": self.token_tracker,
            "output_dir": self.output_dir,
            "logger": self.logger
        }
        # Override base config with any specific kwargs
        config = {**base_config, **kwargs}
        return agent_class(**config) 