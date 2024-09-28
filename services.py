from typing import List, Tuple
from models import ClaimsBorderaux, TreatyStatementInformation, Treaty
from collections import defaultdict
from datetime import date, datetime, timedelta

def parse_date(date_string):
    if date_string == 'N/A':
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

def is_in_quarter(date: datetime, quarter: int) -> bool:
    quarter_months = {
        1: [1, 2, 3],
        2: [4, 5, 6],
        3: [7, 8, 9],
        4: [10, 11, 12]
    }
    return date.month in quarter_months[quarter]

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def claim_to_dict(claim: ClaimsBorderaux) -> dict:
    return {
        'policy_holder_id': claim.policy_holder_id,
        'member_id': claim.member_id,
        'start_date_of_cover': serialize_datetime(claim.start_date_of_cover),
        'end_date_of_cover': serialize_datetime(claim.end_date_of_cover),
        'date_of_claim_treatment_date': serialize_datetime(claim.date_of_claim_treatment_date),
        'date_of_payment_approval_date': serialize_datetime(claim.date_of_payment_approval_date),
        'outpatient_per_family': claim.outpatient_per_family,
        'inpatient_per_family': claim.inpatient_per_family,
        'dental_per_individual': claim.dental_per_individual,
        'optic_per_individual': claim.optic_per_individual,
        'spectacle_frame_per_individual': claim.spectacle_frame_per_individual,
        'death_and_total_permanent_disability_cover_per_individual_claims': claim.death_and_total_permanent_disability_cover_per_individual_claims,
        'total_claims_paid': claim.total_claims_paid
    }

def process_claims(claims_borderauxs: List[ClaimsBorderaux], treaty_statement_info: TreatyStatementInformation, contract: Treaty, quarter: int):
    claims_in_quarter = [
        claim for claim in claims_borderauxs
        if (claim_date := parse_date(claim.date_of_claim_treatment_date)) is not None and is_in_quarter(claim_date, quarter)
    ]
    
    total_claims_paid = sum(claim.total_claims_paid for claim in claims_in_quarter)
    total_premium = treaty_statement_info.total_premium
    
    maximum_cession_percentage = contract.treaty_details[0].maximum_cession / 100
    claim_limit = maximum_cession_percentage * total_premium
    exceeds_limit = total_claims_paid > claim_limit
    
    fraud_checks = {
        'multiple_claims_same_day': defaultdict(list),
        'suspicious_claim_amounts': [],
        'frequent_claimants': defaultdict(int),
        'large_claims': [],
        'duplicate_entries': defaultdict(list),
    }
    
    for claim in claims_in_quarter:
        claim_date = parse_date(claim.date_of_claim_treatment_date)
        if claim_date is None:
            continue  # Skip claims with invalid dates
        
        # Check for multiple claims on the same day
        fraud_checks['multiple_claims_same_day'][claim_date].append(claim)
        
        # Check for suspicious claim amounts (e.g., round numbers)
        if claim.total_claims_paid % 1000 == 0 and claim.total_claims_paid > 10000:
            fraud_checks['suspicious_claim_amounts'].append(claim)
        
        # Track frequent claimants
        fraud_checks['frequent_claimants'][claim.member_id] += 1
        
        # Identify large claims
        if claim.total_claims_paid > 0.1 * total_premium:
            fraud_checks['large_claims'].append(claim)
        
        # Check for duplicate entries
        claim_key = (claim.member_id, serialize_datetime(claim_date), claim.total_claims_paid)
        fraud_checks['duplicate_entries'][claim_key].append(claim)
    
    # Process fraud checks
    fraud_results = {
        'multiple_claims_same_day': [
            (serialize_datetime(date), [claim_to_dict(c) for c in claims]) for date, claims in fraud_checks['multiple_claims_same_day'].items()
            if len(claims) > 3
        ],
        'suspicious_claim_amounts': [claim_to_dict(c) for c in fraud_checks['suspicious_claim_amounts']],
        'frequent_claimants': [
            (member_id, count) for member_id, count in fraud_checks['frequent_claimants'].items()
            if count > 5
        ],
        'large_claims': [claim_to_dict(c) for c in fraud_checks['large_claims']],
        'duplicate_entries': [
            [claim_to_dict(c) for c in claims] for claims in fraud_checks['duplicate_entries'].values()
            if len(claims) > 1
        ],
    }
    
    # Calculate additional statistics
    quarter_days = 92  # Approximate number of days in a quarter
    claim_frequency = len(claims_in_quarter) / quarter_days
    average_claim_amount = total_claims_paid / len(claims_in_quarter) if claims_in_quarter else 0
    
    results = {
        'quarter': quarter,
        'total_claims_paid': total_claims_paid,
        'claim_limit': claim_limit,
        'exceeds_limit': exceeds_limit,
        'fraud_checks': fraud_results,
        'claim_frequency': claim_frequency,
        'average_claim_amount': average_claim_amount,
    }
    
    return results