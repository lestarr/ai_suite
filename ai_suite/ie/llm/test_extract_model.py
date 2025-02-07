from ai_suite.ie.llm.llm_factory import LLMFactory
from ai_suite.ie.models.challenge_models import ChallengeDetails
from ai_suite.ie.llm.extract import extract_with_response_model
from ai_suite.ie.utils.logging import pretty_print_result
import logging
logger = logging.getLogger(__name__)

llm = LLMFactory("openai")
model_name = "gpt-4o-mini"
response_model = ChallengeDetails
#read input
file = "webextract/data/auxxo_old/investor_info_scrapped.txt"
with open(file, "r") as f:
    content = f.read()

#content = " This is some random document"
#extract
extraction_result, usage = extract_with_response_model(content, response_model, llm_client = llm, model = model_name)
result_dict = extraction_result.model_dump()
pretty_print_result(result_dict, response_model_name = "ContentAnalysisDocType", logger = logger )
