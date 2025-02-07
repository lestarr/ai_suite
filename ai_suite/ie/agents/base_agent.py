from typing import Dict, List, Optional
from ai_suite.ie.models.system_models import InfoModel
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
import logging

class BaseAgent:
    """Base class for all agents providing common functionality."""
    
    def __init__(
        self,
        llm_client: Optional[LLMFactory] = None,
        model_name: str = None,
        token_tracker: Optional[TokenUsageTracker] = None,
        output_dir: str = None,
        logger: Optional[logging.Logger] = None,
        **kwargs
    ):
        """
        Initialize base agent.
        
        Args:
            llm_client: LLM factory instance
            model_name: Name of the model to use
            token_tracker: Optional TokenUsageTracker instance (will create new if None)
            output_dir: Optional output directory
            logger: Optional logger instance (will create new if None)
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.token_tracker = token_tracker
        self.output_dir = output_dir
        self.errors = []
        
        # Setup logging
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def process(self, info: InfoModel) -> InfoModel:
        """
        Process input data. Must be implemented by child classes.
        
        Args:
            info: InfoModel instance containing input data and state
            
        Returns:
            Modified InfoModel instance with results
        """
        raise NotImplementedError("Child classes must implement process()")

    def log_section(self, title: str):
        """Log a section header"""
        self.logger.info(f"\n{'='*20} {title} {'='*20}")

    def log_subsection(self, title: str):
        """Log a subsection header"""
        self.logger.info(f"\n{'-'*10} {title} {'-'*10}")

    def log_result(self, result: Dict, result_name: str = "Result"):
        """Log a result dictionary in a structured way."""
        self.logger.info(f"\n{result_name}:")
        for key, value in result.items():
            self.logger.info(f"{key}: {value}")

    def add_error(self, location: str, error_msg: str):
        """Add error to the error list with location and message."""
        self.errors.append({
            "location": location,
            "error": str(error_msg)
        })
        self.logger.error(f"Error in {location}: {error_msg}")

    def track_usage(self, usage: Dict):
        """Track token usage if tracker is available."""
        if self.token_tracker and usage:
            self.token_tracker.add_usage(usage)

    def get_usage_summary(self) -> Dict:
        """Get current token usage summary."""
        if self.token_tracker:
            return self.token_tracker.get_summary()
        return {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'cost_usd': 0.0
        }

    def get_errors(self) -> List[Dict]:
        """Get list of accumulated errors."""
        return self.errors

    def clear_errors(self):
        """Clear the error list."""
        self.errors = []

    def log_errors(self):
        """Log all accumulated errors."""
        if self.errors:
            self.log_subsection("Errors")
            for error in self.errors:
                self.logger.error(f"Location: {error['location']}")
                self.logger.error(f"Error: {error['error']}\n") 