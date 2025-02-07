Help me to showcase our evaluation solution.
Here is high level description of the solution:
## Overview

The evaluation system consists of several components:
1. Ground truth evaluation
2. Result collection and aggregation
3. Visualization and analysis

## Components

### 1. Entity Evaluators (`entity_evaluators.py`)

- `BaseEvaluator`: Abstract base class for evaluators
- `GroundTruthEvaluator`: Compares extracted data against human-annotated ground truth
- `ContentBasedEvaluator`: Validates extraction against source content

Key features:
- Field-by-field comparison
- Structured evaluation results
- Completeness validation
- Detailed error reporting

Visualization (`visualize_results.py`)

Interactive dashboard showing:
- Summary metrics
- Field-level statistics
- Document-level statistics
- Case level statistics
- Raw evaluation results
- Run comparisons of several experimental runs

Here is the main worker of the evaluation system:
class GroundTruthEvaluator(BaseEvaluator):
    def __init__(self, llm_factory, llm_model: str, field_names: str = ""):
        super().__init__(llm_factory, llm_model)
        self.field_names = field_names

    def build_system_prompt(self) -> str:
        return f"""You are an expert at comparing extracted information against ground truth data. Your task is to evaluate the accuracy of extracted information by comparing it to known correct values.

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
4. Ensure that you have evaluated all these fields: {self.field_names}. 
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
            text_chunk=self.field_names,
            **kwargs
        )
        
        self.token_tracker.add_usage(token_usage)
        return completion

And the models which it uses:
class GroundTruthEvaluationResults(BaseModel):
    ground_truth_evaluations: List[GroundTruthEvaluationResult]
    validation_tried: bool = False
class GroundTruthEvaluationResult(BaseModel):
    field_name_ground_truth: str
    field_name_test: str
    ground_truth_entity_core_value: str
    test_entity_core_value: str
    evaluations: List[EvaluationResult]
class EvaluationResult(BaseModel):
    entity_info_missing: bool = Field(..., description="True if info is null, empty, zero or has default value")
    entity_info_correct: bool = Field(..., description="True if the entity matches ground truth or source")
    examples_for_wrong_or_correct: str = Field(..., description="Examples of correct or wrong entity")

I want to showcase the evaluation system and use it as a reference for our services in the website of my company.
Your tasks:
1. Ask me questions for any necessary clarification
2. Formulate a good description and depiction of this evaluation solution, general for any client usecase and understandable for non technical audience.
3. Using examples of aggregated results generate synthetic date to illustrate possible dashboard views. Think about 3 different usecases and generate synthetic data for each: document stats and field stats. The format for these .csv files is following:

document,total,correct,missing,accuracy
data\test\auto_scraped\gemini\asia2gcapital_gemini-1.5-flash-latest_20250117_010819_extracted.json,25,21,13,84.0
data\test\auto_scraped\gpt-4o\asia2gcapital_gpt-4o_20250117_002736_extracted.json,25,20,13,80.0

field,total,correct,missing,accuracy
name,6,6,0,100.0
website,6,6,0,100.0
linkedin,5,5,3,100.0
twitter,4,4,3,100.0
is_alive,5,5,0,100.0
investor_type,6,6,0,100.0
investor_type_classified,5,4,0,80.0
fund_main_location,5,4,0,80.0
industry_focus,6,5,1,83.33333333333334
industry_generalist,4,4,2,100.0
investment_stages_and_rounds,6,2,0,33.33333333333333

Add short description for each usecase what we are evaluation and why.


