"""Validator for ISO 20022 XML financial messages."""

import re
import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import List, Optional, Tuple
from .models import ValidationResult
from .iban_utils import validate_iban

ISO_4217_CURRENCIES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "INR", "SGD",
    "HKD", "SEK", "NOK", "DKK", "NZD", "ZAR", "BRL", "MXN", "AED", "SAR"
}

UETR_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _strip_ns(tag: str) -> str:
    """Strip XML namespace from tag if present."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class ISO20022Validator:
    """Validates structural, financial, and semantic integrity of ISO 20022 documents."""

    def __init__(self):
        pass

    def validate_xml(self, xml_text: str) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"XML Parse Error: {e}"],
            )

        root_tag = _strip_ns(root.tag)
        if root_tag != "Document":
            errors.append(f"Root element must be 'Document', found '{root_tag}'")

        # Extract namespace
        ns_match = re.search(r"\{([^}]+)\}", root.tag)
        ns = ns_match.group(1) if ns_match else ""

        message_type = "unknown"
        if ns:
            for candidate in ["pacs.008", "pacs.009", "camt.053", "pain.001"]:
                if candidate in ns:
                    message_type = candidate
                    break
        else:
            warnings.append("No XML namespace declared on root Document element")

        # Find child message payload
        payload = None
        for child in root:
            payload = child
            break

        if payload is None:
            errors.append("Document element has no child message payload")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Find GrpHdr
        msg_id = None
        declared_nb_txs = 0
        declared_ctrl_sum: Optional[Decimal] = None

        for child in payload.iter():
            tag = _strip_ns(child.tag)
            if tag == "MsgId" and msg_id is None:
                msg_id = child.text
            elif tag == "NbOfTxs" and declared_nb_txs == 0:
                try:
                    declared_nb_txs = int(child.text or 0)
                except ValueError:
                    errors.append(f"Invalid integer in NbOfTxs: '{child.text}'")
            elif tag == "CtrlSum" and declared_ctrl_sum is None:
                try:
                    declared_ctrl_sum = Decimal(child.text or "0.0")
                except Exception:
                    errors.append(f"Invalid decimal in CtrlSum: '{child.text}'")

        # Calculate actual transactions and sum
        calc_txs = 0
        calc_sum = Decimal("0.0")

        # pacs.008 / pacs.009 / pain.001 transactions: CdtTrfTxInf
        tx_elements = [el for el in payload.iter() if _strip_ns(el.tag) == "CdtTrfTxInf"]
        if tx_elements:
            calc_txs = len(tx_elements)
            for el in tx_elements:
                # Find amount
                for sub in el.iter():
                    sub_tag = _strip_ns(sub.tag)
                    if sub_tag in ["IntrBkSttlmAmt", "InstdAmt"]:
                        try:
                            amt_val = Decimal(sub.text or "0.0")
                            calc_sum += amt_val
                        except Exception:
                            errors.append(f"Invalid amount value: '{sub.text}'")

                        # Validate currency
                        ccy = sub.attrib.get("Ccy")
                        if ccy:
                            if ccy.upper() not in ISO_4217_CURRENCIES:
                                warnings.append(f"Non-standard ISO 4217 currency code: '{ccy}'")
                        else:
                            errors.append(f"Missing mandatory 'Ccy' attribute on {sub_tag}")

        # camt.053 statement entries: Ntry
        entry_elements = [el for el in payload.iter() if _strip_ns(el.tag) == "Ntry"]
        if entry_elements and not tx_elements:
            calc_txs = len(entry_elements)
            for el in entry_elements:
                for sub in el.iter():
                    if _strip_ns(sub.tag) == "Amt":
                        try:
                            calc_sum += Decimal(sub.text or "0.0")
                        except Exception:
                            errors.append(f"Invalid statement entry amount: '{sub.text}'")

        # Cross-check transaction count
        if declared_nb_txs > 0 and declared_nb_txs != calc_txs:
            errors.append(
                f"Transaction count mismatch: GrpHdr declared {declared_nb_txs}, but found {calc_txs}"
            )

        # Cross-check control sum
        if declared_ctrl_sum is not None and abs(declared_ctrl_sum - calc_sum) > Decimal("0.0001"):
            errors.append(
                f"Control sum mismatch: GrpHdr declared {declared_ctrl_sum:.2f}, but sum of transactions is {calc_sum:.2f}"
            )

        # Validate IBANs
        for el in payload.iter():
            if _strip_ns(el.tag) == "IBAN":
                iban_val = (el.text or "").strip()
                is_valid_iban, reason = validate_iban(iban_val)
                if not is_valid_iban:
                    errors.append(f"Invalid IBAN '{iban_val}': {reason}")

        # Validate BICs
        for el in payload.iter():
            if _strip_ns(el.tag) == "BICFI":
                bic_val = (el.text or "").strip().upper()
                if len(bic_val) not in (8, 11):
                    errors.append(f"Invalid BIC length '{bic_val}': must be 8 or 11 characters")
                elif not re.match(r"^[A-Z0-9]+$", bic_val):
                    errors.append(f"Invalid characters in BIC '{bic_val}'")

        # Validate UETRs
        for el in payload.iter():
            if _strip_ns(el.tag) == "UETR":
                uetr_val = (el.text or "").strip()
                if not UETR_REGEX.match(uetr_val):
                    errors.append(f"Invalid UETR format: '{uetr_val}' (must be UUIDv4)")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            message_type=message_type,
            message_id=msg_id,
            number_of_transactions=declared_nb_txs,
            calculated_transactions=calc_txs,
            declared_control_sum=declared_ctrl_sum,
            calculated_control_sum=calc_sum,
            errors=errors,
            warnings=warnings,
        )
