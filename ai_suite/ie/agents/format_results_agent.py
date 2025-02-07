from typing import Optional, List, Dict, Type
import pandas as pd
from tabulate import tabulate
import os
import json
from datetime import datetime
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.models.system_models import InfoModel
from ai_suite.ie.utils.url import normalize_url
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.utils import TokenUsageTracker
from pydantic import BaseModel

class FormatResultsAgent(BaseAgent):
    """Agent responsible for loading cached extractions and formatting them into tables/CSV"""
    
    def __init__(
        self,
        output_dir: str,
        model_name: str,
        llm_client: LLMFactory,
        extraction_models: List[str],
        field_mapping: Dict[str, List[str]],  # Maps model name to fields to extract
        token_tracker: TokenUsageTracker = None,
        logger = None,
        display_results: bool = True,
        table_format: str = "pretty",
        truncate_lengths: Dict[str, int] = None  # Optional field truncation lengths
    ):
        super().__init__(llm_client, model_name, token_tracker, logger=logger, output_dir=output_dir)
        self.output_dir = output_dir
        self.display_results = display_results
        self.table_format = table_format
        self.extraction_models = extraction_models
        self.field_mapping = field_mapping
        self.truncate_lengths = truncate_lengths or {}
        self.extractions_dir = os.path.join(output_dir, "extractions", model_name)
        
    def _get_output_path(self, timestamp: str) -> str:
        """Generate path for formatted results"""
        results_dir = os.path.join(self.output_dir, "results", self.model_name)
        os.makedirs(results_dir, exist_ok=True)
        return os.path.join(results_dir, f"challenges_{timestamp}.csv")

    def _load_cached_extraction(self, url: str, model_name: str) -> Optional[List]:
        """Load cached extraction if it exists"""
        try:
            path = os.path.join(self.extractions_dir, f"{normalize_url(url)}_{model_name}.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    model_class = globals()[model_name]
                    return [model_class(**e) for e in data['extractions']]
            return None
        except Exception as e:
            self.logger.warning(f"Failed to load cached extraction for {url}: {e}")
            return None

    def load_cached_results(self, info: InfoModel) -> None:
        """Load cached extractions if they exist"""
        if info.enable_extraction_rerun:
            self.logger.info("Rerun enabled - skipping cache loading")
            return

        loaded_count = 0
        for text in info.texts:
            if not text.source_url:
                continue
                
            self.log_subsection(f"Checking cache for: {text.source_url}")
            for model_name in self.extraction_models:
                cached = self._load_cached_extraction(text.source_url, model_name)
                if cached:
                    text.extractions.extend(cached)
                    loaded_count += len(cached)
                    self.logger.info(f"Loaded {len(cached)} cached {model_name} extractions")

        self.logger.info(f"Total cached extractions loaded: {loaded_count}")

    def _truncate_value(self, field: str, value: str) -> str:
        """Truncate value if length limit exists"""
        max_length = self.truncate_lengths.get(field)
        if max_length and isinstance(value, str) and len(value) > max_length:
            return value[:max_length] + "..."
        return value

    def format_extractions(self, info: InfoModel) -> pd.DataFrame:
        """Format extractions into a DataFrame based on field mapping"""
        rows = []
        for text in info.texts:
            for extraction in text.extractions:
                model_name = extraction.__class__.__name__
                if model_name in self.field_mapping:
                    row = {}
                    for field in self.field_mapping[model_name]:
                        value = getattr(extraction, field, None)
                        row[field] = self._truncate_value(field, str(value))
                    rows.append(row)
        return pd.DataFrame(rows)

    def display_table(self, df: pd.DataFrame):
        """Display DataFrame as a nicely formatted table"""
        print("\nData Found:")
        print(tabulate(
            df,
            headers='keys',
            tablefmt=self.table_format,
            showindex=False
        ))

    async def process(self, info: InfoModel) -> InfoModel:
        """Load cached results, format and save to CSV"""
        self.log_section("Loading and Formatting Results")
        
        try:
            # First load any cached results
            self.load_cached_results(info)
            
            # Then format to DataFrame
            df = self.format_extractions(info)
            
            if df.empty:
                self.logger.warning("No data found to format")
                return info
                
            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self._get_output_path(timestamp)
            df.to_csv(output_path, index=False)
            self.logger.info(f"Saved formatted results to: {output_path}")
            
            # Display if enabled
            if self.display_results:
                self.display_table(df)
            
            return info
            
        except Exception as e:
            self.add_error("FormatResultsAgent.process", str(e))
            self.logger.error(f"Failed to format results: {str(e)}")
            return info 