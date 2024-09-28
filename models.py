from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import date



class CategoryLimit(BaseModel):
    """
    Represents a category limit in the treaty.
    """
    category_number: int = Field(..., description="Category Number in the treaty (1-5)")
    category_name: str = Field(..., description="Name or description of the category (e.g., 'Limit outpatient per family')")
    limit: int = Field(..., description="Limit amount which is after the currency denomination (e.g., Bif (Burundian Franc))")

class TreatyDetail(BaseModel):
    """
    Represents the details of a treaty.
    """
    limits: List[CategoryLimit] = Field(..., description="List of limits for each category number")
    retention_percentage: float = Field(..., description="Percentage of retention for all categories")
    maximum_cession: float = Field(..., description="Maximum cession percentage for all categories")

class Exclusion(BaseModel):
    exclusion_clause: Optional[str] = None
    description: str

class Commission(BaseModel):
    """
    Represents the commission structure in the treaty.
    """
    commission_min: Optional[float] = Field(None, description="Minimum commission percentage")
    commission_max: Optional[float] = Field(None, description="Maximum commission percentage")
    loss_ratio_min: Optional[float] = Field(None, description="Minimum loss ratio percentage")
    loss_ratio_max: Optional[float] = Field(None, description="Maximum loss ratio percentage")

class SpecialCondition(BaseModel):
    """
    Represents a special condition in the treaty.
    """
    condition: str = Field(..., description="Special condition applicable to the treaty")
    description: Optional[str] = Field(None, description="Additional details or description of the special condition")

class LawAndJurisdiction(BaseModel):
    """
    Represents the law and jurisdiction governing the treaty.
    """
    law: str = Field(..., description="Applicable law governing the treaty")
    jurisdiction: str = Field(..., description="Jurisdiction for resolving disputes")

class Arbitration(BaseModel):
    """
    Represents the arbitration details in the treaty.
    """
    seat_of_arbitration: str = Field(..., description="Location of the arbitration proceedings")
    arbitrator_name: Optional[str] = Field(None, description="Name of the arbitrator, if applicable")

class AgeLimit(BaseModel):
    """
    Represents the age limits for policies in the treaty.
    """
    new_policy_age_limit: Optional[int] = Field(None, description="Maximum age limit for new policies")
    renewal_policy_age_limit: Optional[int] = Field(None, description="Maximum age limit for policy renewals")

class Liability(BaseModel):
    """
    Represents the several liability terms in the treaty.
    """
    several_liability: str = Field(..., description="Several liability clause")
    description: Optional[str] = Field(None, description="Explanation or details of the several liability clause")

class ReinsurerParticipation(BaseModel):
    """
    Represents the participation of a reinsurer in the treaty.
    """
    reinsurer_name: str = Field(..., description="Name of the reinsurer (e.g., AFRICAN REINSURANCE CORPORATION, ZEP-RE (PTA REINSURANCE COMPANY LTD), KENYA REINSURANCE CORPORATION)")
    participation_percentage: float = Field(..., description="Percentage of participation by the reinsurer (e.g., 60, 30, 10). Ensure the values are correctly extracted from the document.")

class Intermediary(BaseModel):
    """
    Represents the intermediary handling the treaty.
    """
    intermediary_name: str = Field(..., description="Name of the intermediary handling the treaty")
    brokerage_percentage: Optional[float] = Field(None, description="Brokerage percentage for the intermediary")

class Treaty(BaseModel):
    """
    Represents the treaty details.
    """
    reinsured: str = Field(..., description="Name of the entity being reinsured")
    start_date: date = Field(..., description="Start date of the treaty agreement")
    end_date: date = Field(..., description="End date of the treaty agreement")
    treaty_type: str = Field(..., description="Type of treaty (e.g., quota share, excess of loss, etc.)")
    business_covered: List[str] = Field(..., description="List of types of business covered under the treaty")
    territorial_scope: str = Field(..., description="Geographical area covered by the treaty")
    treaty_details: List[TreatyDetail] = Field(..., description="Details of different categories within the treaty")
    exclusions: Optional[List[Exclusion]] = Field(None, description="List of exclusions applicable to the treaty")
    original_gross_rate: Optional[float] = Field(None, description="Original gross rate applied to the treaty")
    commission: Optional[Commission] = Field(None, description="Details of the commission structure")
    special_conditions: Optional[List[SpecialCondition]] = Field(None, description="Special conditions applicable to the treaty")
    cash_loss_limit: Optional[str] = Field(None, description="Limit for cash losses under the treaty")
    accounts_settlement: Optional[str] = Field(None, description="Details of account settlement terms")
    currency: Optional[str] = Field(None, description="Currency used for the treaty")
    taxes: Optional[str] = Field(None, description="Applicable taxes for the treaty")
    law_and_jurisdiction: Optional[LawAndJurisdiction] = Field(None, description="Law and jurisdiction governing the treaty")
    arbitration: Optional[Arbitration] = Field(None, description="Details of arbitration, if applicable")
    age_limit: Optional[AgeLimit] = Field(None, description="Age limits for new and renewal policies")
    several_liability: Optional[Liability] = Field(None, description="Several liability terms for the treaty")
    intermediary: Optional[Intermediary] = Field(None, description="Details of the intermediary and brokerage")
    reinsurer_participations: List[ReinsurerParticipation] = Field(..., description="List of reinsurers and their participation percentages.")



class PremiumBorderaux(BaseModel):
    policy_holder_id: str = Field(..., description="Policy Holder ID")
    principal_beneficiary: str = Field(..., description="Principal Beneficiary")
    dependants: int = Field(..., description="Number of Dependants")
    total_beneficiaries: int = Field(..., description="Total Beneficiaries")
    police_id: str = Field(..., description="Police ID")
    start_date_of_cover: str = Field(..., description="Start Date of Cover")
    end_date_of_cover: str = Field(..., description="End Date of Cover")
    full_annual_premium_payable: float = Field(..., description="Full Annual Premium Payable")
    number_of_payment_installments_allowed: int = Field(..., description="Number of Payment Installments Allowed")
    amount_payable_per_installment: float = Field(..., description="Amount Payable Per Installment")
    total_premium_paid_to_date: float = Field(..., description="Total Premium Paid to Date")
    outstanding_premium_balance: float = Field(..., description="Outstanding Premium Balance")
    premium_amount: float = Field(..., description="Premium Amount")
    limit_outpatient_per_family: float = Field(..., description="Limit Outpatient per Family")
    limit_inpatient_per_family: float = Field(..., description="Limit Inpatient per Family")
    limit_dental_per_individual: float = Field(..., description="Limit Dental per Individual")
    limit_optic_per_individual: float = Field(..., description="Limit Optic per Individual")
    limit_spectacle_frame_per_individual: float = Field(..., description="Limit Spectacle Frame per Individual")
    death_and_total_permanent_disability_cover_per_individual: float = Field(..., description="Death and Total Permanent Disability Cover per Individual")
    premium_paid_billed: float = Field(..., description="Premium Paid/Billed")

class ClaimsBorderaux(BaseModel):
    policy_holder_id: str = Field(..., description="Policy Holder ID")
    member_id: str = Field(..., description="Member ID")
    start_date_of_cover: str = Field(..., description="Start Date of Cover")
    end_date_of_cover: str = Field(..., description="End Date of Cover")
    date_of_claim_treatment_date: str = Field(..., description="Date of Claim/Treatment Date")
    date_of_payment_approval_date: str = Field(..., description="Date of Payment/Approval Date")

    outpatient_per_family: float = Field(..., description="Outpatient Limit per Family")
    inpatient_per_family: float = Field(..., description="Inpatient Limit per Family")

    dental_per_individual: float = Field(..., description="Dental Limit per Individual")
    optic_per_individual: float = Field(..., description="Optic Limit per Individual")
    spectacle_frame_per_individual: float = Field(..., description="Spectacle Frame Limit per Individual")

    death_and_total_permanent_disability_cover_per_individual_claims: float = Field(..., description="Death and Total Permanent Disability Cover per Individual (Claims)")

    total_claims_paid: float = Field(..., description="Total Claims Paid")

class BorderauxInformation(BaseModel):
    claims_borderaux: List[ClaimsBorderaux]


class TreatyStatementInformation(BaseModel):
    reinsured: str
    treaty: str
    period: str
    total_premium: float
    total_claims: float
    share_balance: float
    share_percentage: float