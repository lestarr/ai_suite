from typing import Optional
import os
import json
from datetime import datetime
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel
from ai_suite.ie.utils.url import normalize_url
from ai_suite.ie.utils.utils import TokenUsageTracker
from ai_suite.ie.llm.llm_factory import LLMFactory
import logging

class SaveExtractionsAgent(BaseAgent):
    """Agent responsible for saving extractions to JSON files"""
    
    def __init__(
        self,
        output_dir: str,
        model_name: str,
        token_tracker: TokenUsageTracker = None,
        logger: logging.Logger = None,
        llm_client: LLMFactory = None
    ):
        super().__init__(llm_client, model_name, token_tracker, logger=logger, output_dir=output_dir)
        self.output_dir = output_dir
        
    def _get_output_path(self, url: str, model_name: str) -> str:
        """Generate path for extraction results"""
        normalized_url = normalize_url(url)
        extractions_dir = os.path.join(self.output_dir, "extractions", self.model_name)
        os.makedirs(extractions_dir, exist_ok=True)
        return os.path.join(extractions_dir, f"{normalized_url}_{model_name}.json")

    async def process(self, info: InfoModel) -> InfoModel:
        """Save all extractions from texts to JSON files"""
        self.log_section("Saving Extractions")
        
        saved_count = 0
        for text in info.texts:
            if not text.source_url or not text.extractions:
                continue
                
            try:
                # Group extractions by model type
                extractions_by_model = {}
                for extraction in text.extractions:
                    model_name = extraction.__class__.__name__
                    if model_name not in extractions_by_model:
                        extractions_by_model[model_name] = []
                    extractions_by_model[model_name].append(extraction)
                
                # Save each model's extractions separately
                for model_name, extractions in extractions_by_model.items():
                    path = self._get_output_path(text.source_url, model_name)
                    
                    data = {
                        'url': text.source_url,
                        'model': model_name,
                        'timestamp': datetime.now().isoformat(),
                        'extractions': [e.model_dump() for e in extractions]
                    }
                    
                    with open(path, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    saved_count += len(extractions)
                    self.logger.info(f"Saved {len(extractions)} {model_name} extractions to {path}")
            
            except Exception as e:
                self.add_error(f"SaveExtractionsAgent.process:{text.source_url}", str(e))
        
        self.logger.info(f"Total extractions saved: {saved_count}")
        
        return info 