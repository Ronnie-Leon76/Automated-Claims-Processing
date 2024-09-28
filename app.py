import streamlit as st
from datetime import datetime
from data_loader import extract_treaty_information_from_documents
from services import process_claims
from models import ClaimsBorderaux, TreatyStatementInformation, Treaty
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import uuid
import hashlib
import redis
import json
import pandas as pd

# Define directory for saving uploaded files
UPLOAD_DIR = "uploaded_files"

REDIS_URL = os.getenv("REDIS_URL")
CACHE_TTL = 432000

redis_client = redis.StrictRedis.from_url(REDIS_URL)

def get_cache_key(file_contents):
    return hashlib.md5(file_contents).hexdigest()

def cache_result(key, result):
    redis_client.setex(key, CACHE_TTL, json.dumps(result))

def get_cached_result(key):
    result = redis_client.get(key)
    if result:
        return json.loads(result.decode())
    return None

# Ensure the directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Streamlit App Implementation
st.title('Claims Processing Application')

# Add information about downloading files
st.info("""
Before proceeding, please download the required files from the following Google Drive link:
[Download Files](https://drive.google.com/drive/folders/1AHOomfMfKPvH6T7Z6LoA5ERI2PNDh_Px?usp=sharing)

You will need to download three files:
1. Contract PDF file
2. Excel file for Borderaux
3. Treaty Slip PDF with Images
""")

# Step 1: Upload three documents
st.header("Upload Documents")

pdf_directory = st.file_uploader("Upload the contract PDF file", type=["pdf"])
excel_file = st.file_uploader("Upload the Excel file for Borderaux", type=["xlsx"])
treaty_pdf_with_images = st.file_uploader("Upload the Treaty Slip PDF with Images", type=["pdf"])

# Step 2: Select quarter and year
st.header("Select Quarter")
quarter = st.selectbox('Select the quarter:', [1, 2, 3, 4])

# Step 3: Process claims
if st.button("Process Claims"):
    if pdf_directory is not None and excel_file is not None and treaty_pdf_with_images is not None:
        try:
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Update progress
            def update_progress(progress, status):
                progress_bar.progress(progress)
                status_text.text(status)

            # Generate cache keys based on file contents
            update_progress(0.1, "Generating cache keys...")
            pdf_key = get_cache_key(pdf_directory.getvalue())
            excel_key = get_cache_key(excel_file.getvalue())
            treaty_key = get_cache_key(treaty_pdf_with_images.getvalue())
            
            combined_key = get_cache_key(f"{pdf_key}-{excel_key}-{treaty_key}".encode())

            # Check if results are already cached
            cached_result = get_cached_result(combined_key)
            
            if cached_result:
                update_progress(0.9, "Retrieved cached results...")
                results = cached_result
            else:
                # Save uploaded files in a permanent directory
                update_progress(0.2, "Saving uploaded files...")
                unique_id = str(uuid.uuid4())
                pdf_path = os.path.join(UPLOAD_DIR, f"contract_{unique_id}.pdf")
                excel_path = os.path.join(UPLOAD_DIR, f"borderaux_{unique_id}.xlsx")
                treaty_path = os.path.join(UPLOAD_DIR, f"treaty_{unique_id}.pdf")

                # Write the uploaded files to the specified paths
                with open(pdf_path, "wb") as f:
                    f.write(pdf_directory.getvalue())
                with open(excel_path, "wb") as f:
                    f.write(excel_file.getvalue())
                with open(treaty_path, "wb") as f:
                    f.write(treaty_pdf_with_images.getvalue())

                # Extract treaty information
                update_progress(0.4, "Extracting information from the documents...")
                treaty_object, borderaux_data, treaty_statement_information = extract_treaty_information_from_documents(pdf_path, excel_path, treaty_path)

                # Process claims
                update_progress(0.7, "Processing claims...")
                results = process_claims(borderaux_data.claims_borderaux, treaty_statement_information, treaty_object, quarter)

                # Cache the results
                cache_result(combined_key, results)

                # Clean up temporary files
                os.remove(pdf_path)
                os.remove(excel_path)
                os.remove(treaty_path)

            # Display results as a report
            update_progress(0.9, "Generating report...")

            st.success("Claims Processing Complete")

            st.header("Claims Processing Report")

            # Quarter Info
            st.header("Period Information")
            st.info(f"**Quarter**: {results['quarter']}")

            # Financial Summary
            st.header("Financial Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Claims Paid", value=f"{results['total_claims_paid']:,.2f}")
            with col2:
                st.metric(label="Claim Limit", value=f"{results['claim_limit']:,.2f}")
            with col3:
                st.metric(label="Exceeds Limit", value="Yes" if results['exceeds_limit'] else "No", 
                        delta="Exceeds" if results['exceeds_limit'] else "Within Limit",
                        delta_color="inverse")

            # Claims Overview
            st.header("Claims Overview")
            fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
            
            # Pie chart for claims vs limit
            fig.add_trace(go.Pie(labels=['Claims Paid', 'Remaining Limit'], 
                                values=[results['total_claims_paid'], max(0, results['claim_limit'] - results['total_claims_paid'])],
                                name="Claims vs Limit"), 1, 1)
            
            # Gauge chart for limit usage
            limit_usage = min(results['total_claims_paid'] / results['claim_limit'] * 100, 100)
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = limit_usage,
                title = {'text': "Limit Usage"},
                gauge = {'axis': {'range': [None, 100]},
                        'steps': [
                            {'range': [0, 60], 'color': "lightgreen"},
                            {'range': [60, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "red"}],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}}), 1, 2)

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Fraud Checks
            st.header("Fraud Detection Results")
            fraud_checks = results['fraud_checks']
            
            if any(fraud_checks.values()):
                for check, data in fraud_checks.items():
                    if data:
                        st.subheader(check.replace('_', ' ').title())
                        if check == 'multiple_claims_same_day':
                            for date, claims in data:
                                st.warning(f"**Date**: {date}")
                                st.table(pd.DataFrame(claims))
                        elif check == 'frequent_claimants':
                            st.table(pd.DataFrame(data, columns=['Member ID', 'Claim Count']))
                        else:
                            st.table(pd.DataFrame(data))
            else:
                st.success("No fraudulent activities detected.")

            # Additional Statistics
            st.header("Additional Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Claim Frequency (per day)", value=f"{results['claim_frequency']:.2f}")
            with col2:
                st.metric(label="Average Claim Amount", value=f"{results['average_claim_amount']:,.2f}")

            # Summary of the Report
            st.header("Report Summary")
            st.markdown(f"""
            - **Total Claims Paid**: {results['total_claims_paid']:,.2f}
            - **Claim Limit**: {results['claim_limit']:,.2f}
            - **Exceeds Limit**: {'Yes' if results['exceeds_limit'] else 'No'}
            - **Fraudulent Activities Detected**: {sum(len(v) for v in fraud_checks.values())}
            - **Claim Frequency**: {results['claim_frequency']:.2f} claims per day
            - **Average Claim Amount**: {results['average_claim_amount']:,.2f}
            """)
            # Complete the progress bar
            update_progress(1.0, "Processing complete!")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.write("Please check the server logs for more details.")
    else:
        st.warning("Please upload all required documents.")