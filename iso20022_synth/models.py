"""Data models for synthetic ISO 20022 messages and validation."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class MessageType(str, Enum):
    PACS_008 = "pacs.008.001.10"
    PACS_009 = "pacs.009.001.09"
    CAMT_053 = "camt.053.001.10"
    PAIN_001 = "pain.001.001.11"


@dataclass
class FinancialParty:
    name: str
    bic: str
    iban: Optional[str] = None
    street: str = "Main Financial Plaza"
    building_number: str = "100"
    postal_code: str = "10001"
    town: str = "New York"
    country: str = "US"


@dataclass
class PaymentTransaction:
    end_to_end_id: str
    uetr: str
    amount: Decimal
    currency: str
    debtor: FinancialParty
    creditor: FinancialParty
    debtor_agent_bic: str
    creditor_agent_bic: str
    settlement_date: str
    remittance_info: str = "Invoice settlement"


@dataclass
class GroupHeader:
    message_id: str
    creation_date_time: str
    number_of_transactions: int
    control_sum: Decimal
    settlement_method: str = "CLRG"
    clearing_system_code: str = "FDN"  # FedNow or SEPA (SCT)


@dataclass
class ValidationResult:
    is_valid: bool
    message_type: Optional[str] = None
    message_id: Optional[str] = None
    number_of_transactions: int = 0
    calculated_transactions: int = 0
    declared_control_sum: Optional[Decimal] = None
    calculated_control_sum: Optional[Decimal] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"Validation Status: {status}",
            f"Message Type: {self.message_type or 'Unknown'}",
            f"Message ID: {self.message_id or 'N/A'}",
            f"Transaction Count: Declared={self.number_of_transactions}, Found={self.calculated_transactions}",
            f"Control Sum: Declared={self.declared_control_sum}, Calculated={self.calculated_control_sum}",
        ]
        if self.errors:
            lines.append("Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)
