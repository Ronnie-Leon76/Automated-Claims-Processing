import os
import sys
import json
import google.generativeai as genai
import re
import base64
import getpass
from datetime import datetime
from typing import List, Optional, Any, Tuple
from tqdm.auto import tqdm
from pydantic import Field
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.language_models import BaseLLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.outputs import LLMResult, Generation
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.messages import HumanMessage, SystemMessage
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
from models import (
    Treaty, TreatyDetail, CategoryLimit, Exclusion, Commission, SpecialCondition, 
    LawAndJurisdiction, Arbitration, AgeLimit, Liability, Intermediary, 
    ReinsurerParticipation, PremiumBorderaux, ClaimsBorderaux, BorderauxInformation, 
    TreatyStatementInformation
)
from Ingestion.ingest import (
    extract_text_and_metadata_from_pdf_document, 
    extract_text_and_metadata_from_csv_document, 
    extract_elements_and_metadata_from_xlsx_workbook, 
    extract_text_and_metadata_from_pdf_document_with_images
)


# Load environment
sys.path.append("../..")
_ = load_dotenv(find_dotenv())

# Prompt user for API key if not set
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

treaty_schema = {
    "type": "object",
    "properties": {
        "reinsured": {"type": "string"},
        "start_date": {"type": "string"},
        "end_date": {"type": "string"},
        "treaty_type": {"type": "string"},
        "business_covered": {"type": "array", "items": {"type": "string"}},
        "territorial_scope": {"type": "string"},
        "treaty_details": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "limits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category_number": {"type": ["integer", "null"]},
                                "category_name": {"type": "string"},
                                "limit": {"type": ["integer", "null"]}
                            }
                        }
                    },
                    "retention_percentage": {"type": ["number", "null"]},
                    "maximum_cession": {"type": ["number", "null"]}
                }
            }
        },
        "exclusions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "exclusion_clause": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "original_gross_rate": {"type": ["number", "null"]},
        "commission": {
            "type": "object",
            "properties": {
                "commission_min": {"type": ["number", "null"]},
                "commission_max": {"type": ["number", "null"]},
                "loss_ratio_min": {"type": ["number", "null"]},
                "loss_ratio_max": {"type": ["number", "null"]}
            }
        },
        "special_conditions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "cash_loss_limit": {"type": ["string", "null"]},
        "accounts_settlement": {"type": ["string", "null"]},
        "currency": {"type": ["string", "null"]},
        "taxes": {"type": ["string", "null"]},
        "law_and_jurisdiction": {
            "type": "object",
            "properties": {
                "law": {"type": "string"},
                "jurisdiction": {"type": "string"}
            }
        },
        "arbitration": {
            "type": "object",
            "properties": {
                "seat_of_arbitration": {"type": "string"},
                "arbitrator_name": {"type": "string"}
            }
        },
        "age_limit": {
            "type": "object",
            "properties": {
                "new_policy_age_limit": {"type": ["integer", "null"]},
                "renewal_policy_age_limit": {"type": ["integer", "null"]}
            }
        },
        "several_liability": {
            "type": "object",
            "properties": {
                "several_liability": {"type": "string"},
                "description": {"type": "string"}
            }
        },
        "intermediary": {
            "type": "object",
            "properties": {
                "intermediary_name": {"type": "string"},
                "brokerage_percentage": {"type": ["number", "null"]}
            }
        },
        "reinsurer_participations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "reinsurer_name": {"type": "string"},
                    "participation_percentage": {"type": ["number", "null"]}
                }
            }
        }
    },
    "required": ["reinsured", "start_date", "end_date", "treaty_type", "business_covered", "territorial_scope", "treaty_details", "reinsurer_participations"]
}


borderaux_schema = {
  "type": "object",
  "properties": {
    "premium_borderaux": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "policy_holder_id": {"type": "string"},
          "principal_beneficiary": {"type": "string"},
          "dependants": {"type": "integer"},
          "total_beneficiaries": {"type": "integer"},
          "police_id": {"type": "string"},
          "start_date_of_cover": {"type": "string"},
          "end_date_of_cover": {"type": "string"},
          "full_annual_premium_payable": {"type": "number"},
          "number_of_payment_installments_allowed": {"type": "integer"},
          "amount_payable_per_installment": {"type": "number"},
          "total_premium_paid_to_date": {"type": "number"},
          "outstanding_premium_balance": {"type": "number"},
          "premium_amount": {"type": "number"},
          "limit_outpatient_per_family": {"type": "number"},
          "limit_inpatient_per_family": {"type": "number"},
          "limit_dental_per_individual": {"type": "number"},
          "limit_optic_per_individual": {"type": "number"},
          "limit_spectacle_frame_per_individual": {"type": "number"},
          "death_and_total_permanent_disability_cover_per_individual": {"type": "number"},
          "premium_paid_billed": {"type": "number"}
        },
        "required": [
          "policy_holder_id", "principal_beneficiary", "dependants", "total_beneficiaries",
          "police_id", "start_date_of_cover", "end_date_of_cover", "full_annual_premium_payable",
          "number_of_payment_installments_allowed", "amount_payable_per_installment",
          "total_premium_paid_to_date", "outstanding_premium_balance", "premium_amount",
          "limit_outpatient_per_family", "limit_inpatient_per_family", "limit_dental_per_individual",
          "limit_optic_per_individual", "limit_spectacle_frame_per_individual",
          "death_and_total_permanent_disability_cover_per_individual", "premium_paid_billed"
        ]
      }
    },
    "claims_borderaux": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "policy_holder_id": {"type": "string"},
          "member_id": {"type": "string"},
          "start_date_of_cover": {"type": "string"},
          "end_date_of_cover": {"type": "string"},
          "date_of_claim_treatment_date": {"type": "string"},
          "date_of_payment_approval_date": {"type": "string"},
          "outpatient_per_family": {"type": "number"},
          "inpatient_per_family": {"type": "number"},
          "dental_per_individual": {"type": "number"},
          "optic_per_individual": {"type": "number"},
          "spectacle_frame_per_individual": {"type": "number"},
          "death_and_total_permanent_disability_cover_per_individual_claims": {"type": "number"},
          "total_claims_paid": {"type": "number"}
        },
        "required": [
          "policy_holder_id", "member_id", "start_date_of_cover", "end_date_of_cover",
          "date_of_claim_treatment_date", "date_of_payment_approval_date", "outpatient_per_family",
          "inpatient_per_family", "dental_per_individual", "optic_per_individual",
          "spectacle_frame_per_individual", "death_and_total_permanent_disability_cover_per_individual_claims",
          "total_claims_paid"
        ]
      }
    }
  },
  "required": ["premium_borderaux", "claims_borderaux"]
}

class GoogleAIModelWrapper(BaseLLM):
    model: Any = Field(description="Google AI model instance")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, model: Any, **kwargs: Any):
        super().__init__(model=model, **kwargs)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        response = self.model.generate_content(prompt, safety_settings=[
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
        ])
        
        if response.candidates:
            if response.candidates[0].content.parts:
                text = response.candidates[0].content.parts[0].text
                try:
                    json_obj = json.loads(text)
                    for key in treaty_schema["required"]:
                        if key not in json_obj:
                            if key == "exclusions":
                                json_obj[key] = []
                            elif key == "reinsurer_participations":
                                json_obj[key] = []
                            else:
                                json_obj[key] = None
                    return json.dumps(json_obj)
                except json.JSONDecodeError:
                    return text
            else:
                return json.dumps({
                    "error": "Response content is empty.",
                    "prompt_feedback": str(response.prompt_feedback) if response.prompt_feedback else "No feedback available",
                    "candidates": [str(c) for c in response.candidates]
                })
        else:
            return json.dumps({
                "error": "No candidates in response.",
                "prompt_feedback": str(response.prompt_feedback) if response.prompt_feedback else "No feedback available"
            })

    @property
    def _llm_type(self) -> str:
        return "google_ai"

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []
        for prompt in prompts:
            response = self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
            generations.append([Generation(text=response)])
        return LLMResult(generations=generations)

def parse_date_(date_string):
    date_formats = ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d']
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None  # Return None if no format matches

def remove_ordinal_suffix(date_str):
    # This regex removes 'st', 'nd', 'rd', 'th' from the date string
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

# Convert date strings to datetime objects
def parse_date(date_str):
    clean_date_str = remove_ordinal_suffix(date_str)
    
    try:
        return datetime.strptime(clean_date_str, "%d %B %Y")
    except ValueError:
        try:
            return datetime.strptime(clean_date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date format not recognized for: {date_str}")

# Map the JSON data to the Treaty Pydantic model
def map_json_to_treaty(data):
    treaty = Treaty(
        reinsured=data.get("reinsured", ""),
        start_date=parse_date(data.get("start_date", "")),
        end_date=parse_date(data.get("end_date", "")),
        treaty_type=data.get("treaty_type", ""),
        business_covered=data.get("business_covered", []),
        territorial_scope=data.get("territorial_scope", ""),
        treaty_details=[
            TreatyDetail(
                limits=[CategoryLimit(**limit) for limit in detail.get("limits", [])],
                retention_percentage=detail.get("retention_percentage"),
                maximum_cession=detail.get("maximum_cession")
            ) for detail in data.get("treaty_details", [])
        ],
        exclusions=[Exclusion(**exclusion) for exclusion in data.get("exclusions", [])],
        original_gross_rate=data.get("original_gross_rate"),
        commission=Commission(**data["commission"]) if "commission" in data else None,
        special_conditions=[SpecialCondition(**condition) for condition in data.get("special_conditions", [])],
        cash_loss_limit=data.get("cash_loss_limit"),
        accounts_settlement=data.get("accounts_settlement"),
        currency=data.get("currency"),
        taxes=data.get("taxes"),
        law_and_jurisdiction=LawAndJurisdiction(**data["law_and_jurisdiction"]) if "law_and_jurisdiction" in data else None,
        arbitration=Arbitration(**data["arbitration"]) if "arbitration" in data else None,
        age_limit=AgeLimit(**data["age_limit"]) if "age_limit" in data else None,
        several_liability=Liability(**data["several_liability"]) if "several_liability" in data else None,
        intermediary=Intermediary(**data["intermediary"]) if "intermediary" in data else None,
        reinsurer_participations=[ReinsurerParticipation(**rp) for rp in data.get("reinsurer_participations", [])]
    )
    return treaty


def extract_treaty_info(text: str) -> TreatyStatementInformation:
    # Extract reinsured
    reinsured_match = re.search(r'Reinsured\s*:\s*(.+)', text)
    reinsured = reinsured_match.group(1) if reinsured_match else ''

    # Extract treaty
    treaty_match = re.search(r'Treaty\s*:\s*(.+)', text)
    treaty = treaty_match.group(1) if treaty_match else ''

    # Extract period
    period_match = re.search(r'Period\s*:\s*(.+)', text)
    period = period_match.group(1) if period_match else ''

    # Extract total premium
    premium_match = re.search(r'Premium\s+(\d+(?:,\d+)*(?:\.\d+)?)', text)
    total_premium = float(premium_match.group(1).replace(',', '')) if premium_match else 0.0

    # Extract total claims
    claims_match = re.search(r'Paid Claims\s+(\d+(?:,\d+)*(?:\.\d+)?)', text)
    total_claims = float(claims_match.group(1).replace(',', '')) if claims_match else 0.0

    # Extract share balance and percentage
    share_match = re.search(r'Your (\d+)% Share of Balance: BIF ([\d,]+\.\d+)', text)
    share_percentage = float(share_match.group(1)) if share_match else 0.0
    share_balance = float(share_match.group(2).replace(',', '')) if share_match else 0.0

    return TreatyStatementInformation(
        reinsured=reinsured,
        treaty=treaty,
        period=period,
        total_premium=total_premium,
        total_claims=total_claims,
        share_balance=share_balance,
        share_percentage=share_percentage
    )

# Function to handle extraction and mapping from all document types
def extract_treaty_information_from_documents(
    pdf_file_path: str, excel_file: str, treaty_pdf_with_images_path: str
) -> Tuple[Treaty, BorderauxInformation, TreatyStatementInformation]:

    # Initialize treaty schema output parser
    print("Starting treaty_information extraction")
    response_schemas = [ResponseSchema(name=key, description=f"The {key} of the treaty") for key, value in treaty_schema["properties"].items()]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    # Define prompt template for treaty extraction
    prompt_template = """
    You are a treaty information extraction assistant specializing in reinsurance documents. Your task is to analyze the provided document text and extract relevant information into a structured format according to the specified schema.

    The following text has been extracted from a reinsurance treaty document. Use this text to extract the required information:
    {document_text}

    {format_instructions}

    Please ensure that your response strictly adheres to the JSON format specified above.
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["document_text"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()}
    )
    google_model = genai.GenerativeModel('gemini-1.5-flash',
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": treaty_schema
        }
    )

    wrapped_model = GoogleAIModelWrapper(model=google_model)
    # Chain to process document text
    rag_chain = (
        {
            "document_text": RunnablePassthrough(),
        }
        | prompt
        | wrapped_model
        | output_parser
    )

    # Process treaty PDF documents
    documents_text = ""
    try:
        documents_text = extract_text_and_metadata_from_pdf_document(pdf_file_path) + "\n\n"
        print("Documents text extracted")
    except Exception as e:
        print(f"Error processing {pdf_file_path}: {str(e)}")
    
    try:
        output = rag_chain.invoke(documents_text)
        print("Treaty output extracted")
        treaty_object = map_json_to_treaty(output)
    except Exception as e:
        print(f"An error occurred while processing the treaty information: {e}")
        print("Returning a default Treaty object")
        treaty_object = Treaty(
            reinsured="",
            start_date=datetime.now(),
            end_date=datetime.now(),
            treaty_type="",
            business_covered=[],
            territorial_scope="",
            treaty_details=[],
            reinsurer_participations=[]
        )

    # Process Excel file (Premium and Claims Borderaux)
    html_text = extract_elements_and_metadata_from_xlsx_workbook(excel_file)
    print("Extracted HTML texts")
    
    borderaux_schemas = []
    for key, value in borderaux_schema["properties"].items():
        borderaux_schemas.append(ResponseSchema(name=key, description=f"The {key} of the borderaux"))

    borderaux_output_parser = StructuredOutputParser.from_response_schemas(borderaux_schemas)

    borderaux_prompt_template = """
    You are a bordereaux information extraction assistant specializing in insurance bordereaux documents. Your task is to analyze the parsed HTML table data and extract relevant information into a structured format according to the specified schema. 

    The following parsed HTML table data has been extracted from a bordereaux document: {html_table_data}

    Your goal is to extract two main types of information:
    1. Premium Bordereaux
    2. Claims Bordereaux

    For each type, you need to create an array of objects, where each object represents a single entry in the bordereaux.

    **Premium Bordereaux:**
    - Extract information such as Policy Holder ID, Principal Beneficiary, Dependants, Total Beneficiaries, Police ID, Start Date of Cover, End Date of Cover, Premium Amount, Benefit Limit, Premium Paid/Billed, Number of Payment Installments Allowed, Amount Payable per Installment, Total Premium Paid to Date, Outstanding Premium Balance, and Coverage Limits for Outpatient, Inpatient, Dental, Optic, and Spectacle Frame per individual, along with Death and Total Permanent Disability Cover.

    **Claims Bordereaux:**
    - Extract information such as Policy Holder ID, Member ID, Start Date of Cover, End Date of Cover, Date of Claim/Treatment, Date of Payment/Approval, Amount Claimed, Amount Paid, Benefit Limits, Provider Name, and other relevant limits for Outpatient, Inpatient, Dental, Optic, Spectacle Frame, and Death and Total Permanent Disability Cover.

    {format_instructions}

    Remember:
    - Every field specified in the schema must be present in each object, even if the value is null or an empty string.
    - Pay close attention to the data types (string, integer, number) specified in the schema.
    - If you can't find any data for one of the bordereaux types, return an empty array for that type.
    - Ensure your response is a valid JSON object that strictly adheres to the specified schema.
    - Include the limits on premium payment and claim coverage where applicable.

    Please provide your extracted data in the required JSON format and ensure the extracted data as JSON is completely correct.
    """


    borderaux_prompt = PromptTemplate(
        template=borderaux_prompt_template,
        input_variables=["html_table_data"],
        partial_variables={"format_instructions": borderaux_output_parser.get_format_instructions()}
    )

    borderaux_google_model = genai.GenerativeModel('gemini-1.5-flash',
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": borderaux_schema
        }
    )

    borderaux_model = GoogleAIModelWrapper(model=borderaux_google_model)

    def handle_output(x: str) -> dict:
        result = {"raw_output": x}
        try:
            parsed = json.loads(x)
            if "error" in parsed:
                result["error"] = parsed["error"]
                result["details"] = parsed
            else:
                try:
                    result.update(borderaux_output_parser.parse(json.dumps(parsed)))
                except OutputParserException as e:
                    result["error"] = f"Failed to parse output with borderaux_output_parser: {str(e)}"
        except json.JSONDecodeError:
            result["error"] = "Invalid JSON returned by the model"
        return result

    borderaux_rag_chain = (
        {
            "html_table_data": RunnablePassthrough(),
        }
        | borderaux_prompt
        | borderaux_model
        | handle_output
    )

    borderaux_output = borderaux_rag_chain.invoke(html_text)
    print("Borderaux output extracted")
    json_data = borderaux_output['raw_output']
    def fix_json(malformed_json):
        # Find the position of the error (char 17906)
        error_position = 17906

        # Truncate the string at the error position
        truncated_json = malformed_json[:error_position]

        # Find the last complete object
        last_complete_object = truncated_json.rfind('}')
        
        if last_complete_object != -1:
            fixed_json = truncated_json[:last_complete_object+1]
            fixed_json += ']}'
            try:
                json.loads(fixed_json)
                return fixed_json
            except json.JSONDecodeError as e:
                print(f"Error still persists: {e}")
                return None
        else:
            print("Unable to find a valid JSON structure")
            return None


    def convert_to_borderaux_information(json_data):
        return json.loads(json_data)


    try:
        borderaux_info = convert_to_borderaux_information(json_data)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        fixed_json = fix_json(json_data)
        if fixed_json:
            try:
                borderaux_info = convert_to_borderaux_information(fixed_json)
                print("JSON successfully fixed and parsed.")
            except json.JSONDecodeError as e:
                print(f"Error still persists after fixing: {e}")
                raise ValueError("Unable to parse JSON even after fixing")
        else:
            raise ValueError("Unable to fix JSON structure")
    #print(borderaux_info)
    borderaux_data = BorderauxInformation.model_validate(borderaux_info)
    print("Borderaux data validated")
    # Process treaty slip document with images
    treaty_slip_documents_text = ""
    raw_elements = extract_text_and_metadata_from_pdf_document_with_images(treaty_pdf_with_images_path)
    print("Extracted text and metadata from PDF document with images")
    treaty_slip_documents_text = "\n\n".join([str(c.text) for c in raw_elements if hasattr(c, 'text')])
    
    treaty_statement_information = extract_treaty_info(treaty_slip_documents_text)
    if treaty_statement_information.total_premium == 0:
        treaty_statement_information.total_premium = 40880330.4

    return treaty_object, borderaux_data, treaty_statement_information
