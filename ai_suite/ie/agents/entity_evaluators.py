from pydantic import BaseModel, Field, model_validator, ValidationInfo
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from extraction.extract import ask_LLM
import os
import time
from extraction.utils import TokenTracker

# Common Models
class EvaluationResult(BaseModel):
    entity_info_missing: bool = Field(..., description="True if info is null, empty, zero or has default value")
    entity_info_correct: bool = Field(..., description="True if the entity matches ground truth or source")
    examples_for_wrong_or_correct: str = Field(..., description="Examples of correct or wrong entity")
    #entity_info_partial: bool = Field(..., description="True if entity is partially correct")
    #explanation_partial: str = Field(..., description="Explanation for partial correctness")

class MissingFieldResult(BaseModel):
    fieldname: str = Field(..., description="Name of the missing field")
    explanation: str = Field(..., description="Explanation of what is missing")
    description: str = Field(..., description="Description of what this field should contain")

class MissingFieldResults(BaseModel):
    missing_fields: List[MissingFieldResult]

class ContentEvaluationResult(BaseModel):
    field_name: str
    evaluations: List[EvaluationResult]

class ContentEvaluationResults(BaseModel):
    content_evaluations: List[ContentEvaluationResult]

class GroundTruthEvaluationResult(BaseModel):
    field_name_ground_truth: str
    field_name_test: str
    ground_truth_entity_core_value: str
    test_entity_core_value: str
    evaluations: List[EvaluationResult]

class GroundTruthEvaluationResults(BaseModel):
    ground_truth_evaluations: List[GroundTruthEvaluationResult]
    validation_tried: bool = False

    @model_validator(mode="after")
    def validate_citation(self) -> "GroundTruthEvaluationResults":
        # collect names of the evaluated fields
        seen_fields = []
        for evaluation in self.ground_truth_evaluations:
            if evaluation.field_name_ground_truth not in seen_fields:
                seen_fields.append(evaluation.field_name_test)
        if len(seen_fields) > 0:
            self.validation_tried = True
        return self


class BaseEvaluator:
    def __init__(self, llm_factory, llm_model: str):
        self.llm = llm_factory
        self.llm_model = llm_model
        self.token_tracker = TokenTracker()

    def build_system_prompt(self) -> str:
        raise NotImplementedError

    def build_context(self, *args, **kwargs) -> Dict:
        raise NotImplementedError

    async def evaluate(self, *args, **kwargs):
        raise NotImplementedError
    
    def output(self, results: BaseModel, file_name: str):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_directory = f"data/evaluation_results/{file_name}"
        os.makedirs(base_directory, exist_ok=True)
        
        # Add token usage to results
        results_dict = results.model_dump()
        results_dict['token_usage'] = self.token_tracker.get_usage()
        
        file_name = f"{self.__class__.__name__}_{timestamp}.json"
        file_path = os.path.join(base_directory, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(results.model_dump_json())
            
        # Print token usage
        self.token_tracker.print_usage(self.__class__.__name__)

class MissingFieldsEvaluator(BaseEvaluator):
    def build_system_prompt(self) -> str:
        return """You are an expert at analyzing data completeness. Your task is to identify missing or null information in the provided JSON data.

Rules for evaluation:
1. Check for null values, empty strings, empty lists, and default values
2. For each missing field, provide:
   - The field name
   - What exactly is missing (whole field, specific feature, etc.)
   - A description of what information this field should contain
3. Consider nested structures and check all levels
4. Ignore validation and citation fields

Please analyze the provided JSON and identify all missing information."""

    def build_context(self, extracted_data: Dict) -> Dict:
        return {
            "data": extracted_data,
            "task": "identify_missing_fields"
        }

    async def evaluate(self, extracted_data: Dict, **kwargs) -> MissingFieldResults:
        prompt = self.build_system_prompt()
        context = self.build_context(extracted_data)
        
        completion, token_usage = ask_LLM(
            content=str(context),
            prompt=prompt,
            response_model=MissingFieldResults,
            llm=self.llm,
            model=self.llm_model,
            **kwargs
        )
        
        self.token_tracker.add_usage(token_usage)
        return completion

class ContentBasedEvaluator(BaseEvaluator):
    def build_system_prompt(self) -> str:
        return """You are an expert at evaluating information extraction quality. Your task is to verify if the extracted information matches the source text content.

Entity Types to Consider:
1. Simple Content Entities: Verify text/numeric values 
2. Boolean/Flag Entities: Verify if flags are supported by text
3. Enumeration Entities: Verify both content and classification
4. Complex Nested Entities: Evaluate all components together
5. List Entities: Evaluate each item separately

For each entity, determine:
1. If information is missing (null/empty/zero)
2. If information is correct based on source text. Evaluate only semantic match with the ground truth, ignore validation, citations and formatting.
3. If information is partially correct
4. Provide explanations for your decisions

Ignore validation and citation fields in your evaluation.
If there are multiple entities and lists, repeat this structure for each, so we have a complete evaluation breakdown."""

    def build_context(self, extracted_data: Dict, source_text: str) -> Dict:
        return {
            "extracted_data": extracted_data,
            "source_text": source_text,
            "task": "evaluate_against_source"
        }

    async def evaluate(self, extracted_data: Dict, source_text: str, **kwargs) -> ContentEvaluationResults:
        prompt = self.build_system_prompt()
        context = self.build_context(extracted_data, source_text)
        
        completion, token_usage = ask_LLM(
            content=str(context),
            prompt=prompt,
            response_model=ContentEvaluationResults,
            llm=self.llm,
            model=self.llm_model,
            **kwargs
        )
        
        self.token_tracker.add_usage(token_usage)
        return completion

class GroundTruthEvaluator(BaseEvaluator):
    def build_system_prompt(self) -> str:
        return """You are an expert at comparing extracted information against ground truth data. Your task is to evaluate the accuracy of extracted information by comparing it to known correct values.

Key Responsibilities:
1. Map fields between test and ground truth data intelligently
2. Handle different label names for the same concepts
3. Determine core parts of the entity that are important for evaluation
4. Evaluate each entity type appropriately with the core parts:
   - Simple Content Entities: match when content is semantically the same
   - Boolean/Flags containing Entities: match when flag in test data matches flag in ground truth
   - Complex Nested Entities: match when content semantically matches and all enum categories match
   - Lists: Compare each item separately
5. Ignore all other fields in your evaluation. E.g. ignore validation, citations, source and formatting.

For each field pair, determine:
1. its label in the ground truth data
2. its label in the test data
3. core parts of the entity that are important for evaluation in the ground truth data
4. core parts of the entity that are important for evaluation in the test data
5. If test data is missing information
6. If test data matches ground truth, consider only semantic match with the ground truth, ignore validation, citations and formatting.
7. Provide examples of correct or wrong entity

Evaluation rules:
1. Ignore validation, citation, explanation, source fields and the formattings in your comparison.
2. If there are multiple entities of one type, e.g. multiple restrictions, etc., repeat this structure for each, so we have a complete evaluation breakdown.
3. You have to ignore the field 'citation' in your comparison, but you have to evaluate ALL the fields which contain 'citation' as their feature
4. Ensure that you have evaluated all these fields: name, website, linkedin, twitter, is_alive, investor_type, investor_type_classified, fund_main_location, industry_focus, industry_generalist, investment_stages_and_rounds, stages_generalist, geo_generalist, russian_affiliated, how_to_pitch, restrictions, startups, members, money_info, check_min, check_max, check_average, assets_under_management, fund_size, fund_raised_date. 
5. Group restrictions on their target groups, so the entity to evaluate would be restriction.target_group. Evaluate each target group separately. Restriction is regarded as correct if the regarded target group is present, its policy is the same as in the ground truth, and its content semantically matches the content of the corresponding target group restrictions in the ground truth.
"""

    def build_context(self, extracted_data: Dict, ground_truth: Dict) -> Dict:
        return {
            "test_data": extracted_data,
            "ground_truth": ground_truth,
            "task": "evaluate_against_ground_truth"
        }

    async def evaluate(self, extracted_data: Dict, ground_truth: Dict, **kwargs) -> GroundTruthEvaluationResults:
        prompt = self.build_system_prompt()
        context = self.build_context(extracted_data, ground_truth)
        
        completion, token_usage = ask_LLM(
            content=str(context),
            prompt=prompt,
            response_model=GroundTruthEvaluationResults,
            llm=self.llm,
            model=self.llm_model,
            **kwargs
        )
        
        self.token_tracker.add_usage(token_usage)
        return completion

# Usage example
async def main():
    from extraction.llm_factory import LLMFactory
    from extraction.utils import load_file_content, load_json_from_file

    llm_factory = LLMFactory("openai")
    llm_model = "gpt-4o"
    
    # Initialize evaluators
    missing_fields_eval = MissingFieldsEvaluator(llm_factory, llm_model)
    content_eval = ContentBasedEvaluator(llm_factory, llm_model)
    ground_truth_eval = GroundTruthEvaluator(llm_factory, llm_model)
    
    # Example evaluations
    # assess missing fields
    # input_file = "merged_5gventures.gr.json"
    # extracted_data = load_json_from_file(f"data/dec_2024/extracted_jsons_jan2025/{input_file}")
    # missing_fields = await missing_fields_eval.evaluate(extracted_data) 
    # print("======= MISSING FIELDS ======= ")
    # print(missing_fields)
    # missing_fields_eval.output(missing_fields, f"{input_file}_{llm_model}")

    # assess content
    # input_file = "merged_5gventures.gr.json"
    # extracted_data = load_json_from_file(f"data/dec_2024/extracted_jsons_jan2025/{input_file}")
    # source_text = load_file_content("data/dec_2024/merged_websites/merged_5gventures.gr.md")
    # content_results = await content_eval.evaluate(extracted_data, source_text)
    # print("======= CONTENT ======= ")
    # print(content_results)
    # content_eval.output(content_results, f"{input_file}_{llm_model}")

    # assess ground truth
    test_file = "atpfund_gemini-1.5-flash-latest_20250117_005515_extracted.json"
    test_file = "btqventures_gpt-4o_20250117_002438_extracted.json"
    ground_truth_file = "atpfund_gemini-1.5-flash-latest_20250117_005515_extracted_auto_Hrushchynska.json"
    ground_truth_file = "btqventures_gpt-4o_20250117_002438_extracted_auto_Hrushchynska.json"
    test_file = "merged_exfinityventures.com.json"
    ground_truth_file = "merged_exfinityventures.com_manual_Hrushchynska.json"
    extracted_data = load_json_from_file(f"data/test/{test_file}")
    ground_truth_data = load_json_from_file(f"data/test/{ground_truth_file}")
    ground_truth_results = await ground_truth_eval.evaluate(extracted_data, ground_truth_data)
    print("======= GROUND TRUTH ======= ")
    print(ground_truth_results)
    ground_truth_eval.output(ground_truth_results, f"{test_file}_{llm_model}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
