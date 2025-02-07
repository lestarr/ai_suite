from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from ai_suite.ie.agents.base_agent import BaseAgent
from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.utils.json_utils import pretty_print_json
import json

class ExtractionEvaluationResult(BaseModel):
    reference_field_name: str
    reference_field_value: Union[str, int, float, bool, List[Any], None] = Field(default=None)
    test_field_name: str
    test_field_value: Union[str, int, float, bool, List[Any], None] = Field(default=None)
    correctness: bool
    explanation: str

class EvaluationMetrics(BaseModel):
    """Pydantic model for evaluation results"""
    evaluation_results: List[ExtractionEvaluationResult]

EVALUATION_PROMPT = """You are an expert data quality evaluator. Compare the test JSON output against the reference JSON and evaluate its quality.

The reference JSON is the ground truth and the test JSON is the output of an extraction model. The namings of the fields in jsons and their structure can differ. If you are able to find a semantically equivalent field name in the test JSON, you should mark it as correct.

Rules for evaluation:
1. Ignore helper fields like validation, citation, content_validation, explanation
2. Include only fields that contain important information to extract
3. Values can be strings, numbers, booleans, lists, or null
4. For list values, produce a list of evaluation results, one for each element
5. Field names that are semantically equivalent should be treated as correct matches
6. Field values that are semantically equivalent should be treated as correct matches

For each field comparison, provide:
- reference_field_name: name of the field in reference JSON
- reference_field_value: transformed and normalized value from reference JSON 
- test_field_name: corresponding field name found in test JSON (or most similar)
- test_field_value: transformed and normalized value from test JSON 
- correctness: boolean indicating if the values match semantically
- explanation: brief explanation of the comparison and decision

Reference JSON:
{reference_json}

Test JSON:
{test_json}

Format your response exactly according to the provided response model, ensuring values maintain their original types (strings, numbers, lists, etc).
"""

class EvaluationAgent(BaseAgent):
    """Agent for evaluating extraction results against reference data"""
    
    def process(self, reference_json: Dict, test_json: Dict) -> EvaluationMetrics:
        """
        Evaluate test JSON against reference JSON using LLM.
        
        Args:
            reference_json: Reference/ground truth JSON
            test_json: Test JSON to evaluate
            
        Returns:
            EvaluationMetrics containing detailed evaluation results
        """
        try:
            self.log_section("Starting JSON Evaluation")
            
            # Format the evaluation prompt
            prompt = EVALUATION_PROMPT.format(
                reference_json=json.dumps(reference_json, indent=2),
                test_json=json.dumps(test_json, indent=2)
            )
            
            # Get evaluation from LLM
            result, usage = extract_with_response_model(
                prompt,
                response_model=EvaluationMetrics,
                llm_client=self.llm_client,
                model=self.model_name
            )
            
            # Track token usage
            self.track_usage(usage)
            
            # Log results
            self.log_result(result.model_dump(), "Evaluation Results")
            
            return result
            
        except Exception as e:
            self.add_error("EvaluationAgent.process", str(e))
            raise

if __name__ == "__main__":
    # Example usage
    reference = {
        "name": "John Doe",
        "age": 30,
        "occupation": "Engineer",
        "investors": ["Investor A", "Investor B", "Investor C"]
    }
    
    test = {
        "name": "John Doe",
        "age": 31,
        "title": "Engineer",
        "investors": ["Investor A", "Investor C", "Investor B"]
    }
    
    llm = LLMFactory("openai")
    agent = EvaluationAgent(llm, "gpt-4o-mini")
    
    result = agent.process(reference, test)
    pretty_print_json(result.model_dump()) 