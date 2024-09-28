import os
import pandas as pd
from collections import defaultdict
from bs4 import BeautifulSoup
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.csv import partition_csv
from unstructured.partition.xlsx import partition_xlsx
import unstructured_client
from unstructured_client.models import operations, shared
from dotenv import load_dotenv, find_dotenv


_ = load_dotenv(find_dotenv())

class UnstructuredAPIProcessor:
    def __init__(self):
        api_key = os.getenv('UNSTRUCTURED_API_KEY')
        server_url = os.getenv('UNSTRUCTURED_API_URL', 'https://api.unstructuredapp.io')
        self.client = unstructured_client.UnstructuredClient(
            api_key_auth=api_key,
            server_url=server_url
        )

    def _process_file(self, file_path, strategy=shared.Strategy.HI_RES, languages=['eng']):
        with open(file_path, "rb") as f:
            data = f.read()
        
        req = operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=shared.Files(
                    content=data,
                    file_name=file_path,
                ),
                strategy=strategy,
                languages=languages,
            ),
        )
        
        try:
            res = self.client.general.partition(request=req)
            return res.elements
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None


def extract_text_and_metadata_from_pdf_document_with_images(pdf_path):
    """
    Extracts text and metadata from a pdf document
    :param pdf_path: path to the pdf document
    :return: tuple of (elements)
    """
    elements = partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        hi_res_model_name="yolox",
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=1000000,
        new_after_n_chars=1000000,
        combine_text_under_n_chars=1000000,
    )
    text_elements = [str(c.text) for c in elements if hasattr(c, 'text')]
    return ' '.join(text_elements)


def extract_text_and_metadata_from_pdf_document(pdf_path):
    """
    Extracts text from a pdf document
    :param pdf_path: path to the pdf document
    :return: string containing all text from the PDF
    """
    elements = partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        hi_res_model_name="yolox",
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=1000000,
        new_after_n_chars=1000000,
        combine_text_under_n_chars=1000000,
    )
    text_elements = [str(c.text) for c in elements if hasattr(c, 'text')]
    return ' '.join(text_elements)

def extract_text_and_metadata_from_csv_document(csv_path):
    """
    Extracts text from a csv document
    :param csv_path: path to the csv document
    :return: string containing all text from the CSV
    """
    processor = UnstructuredAPIProcessor()
    elements = processor._process_file(csv_path, strategy=shared.Strategy.AUTO)
    
    if elements:
        return ' '.join([str(e.text) for e in elements if hasattr(e, 'text')])
    return ""


def extract_elements_and_metadata_from_xlsx_workbook(xlsx_path):
    """
    Extracts HTML content from an xlsx workbook and creates separate dataframes for each element.
    The data is extracted solely from the HTML content.
    
    :param xlsx_path: path to the xlsx workbook
    :return: dict of pandas dataframes with extracted elements and metadata
    """
    elements = partition_xlsx(
        filename=xlsx_path,
        infer_table_structure=True,
    )

    html_text = []
    for element in elements:
        if hasattr(element.metadata, 'text_as_html') and element.metadata.text_as_html:
            html_text.append(element.metadata.text_as_html)

    return html_text