"""Synthetic ISO 20022 XML financial message generators."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import List, Optional
from .models import FinancialParty, PaymentTransaction, MessageType
from .iban_utils import generate_valid_iban, generate_valid_bic


def format_xml(elem: ET.Element) -> str:
    """Return pretty-printed XML string with XML declaration."""
    rough_string = ET.tostring(elem, encoding="utf-8")
    reparsed = xml.dom.minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def create_sample_party(name: str, country: str = "DE") -> FinancialParty:
    return FinancialParty(
        name=name,
        bic=generate_valid_bic(country),
        iban=generate_valid_iban(country),
        country=country,
    )


def generate_pacs008(
    transactions: Optional[List[PaymentTransaction]] = None,
    count: int = 1,
    currency: str = "USD",
    base_amount: Decimal = Decimal("2500.00"),
) -> str:
    """Generate ISO 20022 pacs.008.001.10 (FI To FI Customer Credit Transfer)."""
    ns = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10"
    doc = ET.Element("Document", xmlns=ns)
    root = ET.SubElement(doc, "FIToFICstmrCdtTrf")

    now = datetime.now(timezone.utc)
    msg_id = f"MSG{now.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    if transactions is None:
        transactions = []
        for i in range(count):
            amt = base_amount + Decimal(i * 100)
            uetr = str(uuid.uuid4())
            e2e = f"E2E-{now.strftime('%Y%m%d')}-{i+1:04d}"
            tx = PaymentTransaction(
                end_to_end_id=e2e,
                uetr=uetr,
                amount=amt,
                currency=currency,
                debtor=create_sample_party(f"Acme Corp Client {i+1}", "DE"),
                creditor=create_sample_party(f"Global Supplies Ltd {i+1}", "GB"),
                debtor_agent_bic=generate_valid_bic("DE"),
                creditor_agent_bic=generate_valid_bic("GB"),
                settlement_date=now.strftime("%Y-%m-%d"),
                remittance_info=f"Commercial Invoice #{1000 + i}",
            )
            transactions.append(tx)

    total_sum = sum(tx.amount for tx in transactions)

    # Group Header
    grp_hdr = ET.SubElement(root, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = msg_id
    ET.SubElement(grp_hdr, "CreDtTm").text = now.isoformat()
    ET.SubElement(grp_hdr, "NbOfTxs").text = str(len(transactions))
    ET.SubElement(grp_hdr, "CtrlSum").text = f"{total_sum:.2f}"
    sttlm_inf = ET.SubElement(grp_hdr, "SttlmInf")
    ET.SubElement(sttlm_inf, "SttlmMtd").text = "CLRG"
    clr_sys = ET.SubElement(sttlm_inf, "ClrSys")
    ET.SubElement(clr_sys, "Prtry").text = "FDN"

    # Transactions
    for tx in transactions:
        tx_inf = ET.SubElement(root, "CdtTrfTxInf")
        pmt_id = ET.SubElement(tx_inf, "PmtId")
        ET.SubElement(pmt_id, "EndToEndId").text = tx.end_to_end_id
        ET.SubElement(pmt_id, "UETR").text = tx.uetr

        amt_el = ET.SubElement(tx_inf, "IntrBkSttlmAmt", Ccy=tx.currency)
        amt_el.text = f"{tx.amount:.2f}"
        ET.SubElement(tx_inf, "IntrBkSttlmDt").text = tx.settlement_date

        # Debtor
        dbtr = ET.SubElement(tx_inf, "Dbtr")
        ET.SubElement(dbtr, "Nm").text = tx.debtor.name
        dbtr_acct = ET.SubElement(tx_inf, "DbtrAcct")
        dbtr_id = ET.SubElement(dbtr_acct, "Id")
        ET.SubElement(dbtr_id, "IBAN").text = tx.debtor.iban

        # Debtor Agent
        dbtr_agt = ET.SubElement(tx_inf, "DbtrAgt")
        fin_inst = ET.SubElement(dbtr_agt, "FinInstnId")
        ET.SubElement(fin_inst, "BICFI").text = tx.debtor_agent_bic

        # Creditor Agent
        cdtr_agt = ET.SubElement(tx_inf, "CdtrAgt")
        fin_inst_c = ET.SubElement(cdtr_agt, "FinInstnId")
        ET.SubElement(fin_inst_c, "BICFI").text = tx.creditor_agent_bic

        # Creditor
        cdtr = ET.SubElement(tx_inf, "Cdtr")
        ET.SubElement(cdtr, "Nm").text = tx.creditor.name
        cdtr_acct = ET.SubElement(tx_inf, "CdtrAcct")
        cdtr_id = ET.SubElement(cdtr_acct, "Id")
        ET.SubElement(cdtr_id, "IBAN").text = tx.creditor.iban

        # Remittance
        rmt_inf = ET.SubElement(tx_inf, "RmtInf")
        ET.SubElement(rmt_inf, "Ustrd").text = tx.remittance_info

    return format_xml(doc)


def generate_pacs009(
    count: int = 1,
    currency: str = "EUR",
    base_amount: Decimal = Decimal("500000.00"),
) -> str:
    """Generate ISO 20022 pacs.009.001.09 (Financial Institution Credit Transfer)."""
    ns = "urn:iso:std:iso:20022:tech:xsd:pacs.009.001.09"
    doc = ET.Element("Document", xmlns=ns)
    root = ET.SubElement(doc, "FICdtTrf")

    now = datetime.now(timezone.utc)
    msg_id = f"FI{now.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    total_sum = base_amount * count

    # Group Header
    grp_hdr = ET.SubElement(root, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = msg_id
    ET.SubElement(grp_hdr, "CreDtTm").text = now.isoformat()
    ET.SubElement(grp_hdr, "NbOfTxs").text = str(count)
    ET.SubElement(grp_hdr, "CtrlSum").text = f"{total_sum:.2f}"
    sttlm_inf = ET.SubElement(grp_hdr, "SttlmInf")
    ET.SubElement(sttlm_inf, "SttlmMtd").text = "CLRG"

    for i in range(count):
        tx_inf = ET.SubElement(root, "CdtTrfTxInf")
        pmt_id = ET.SubElement(tx_inf, "PmtId")
        ET.SubElement(pmt_id, "EndToEndId").text = f"TREASURY-{now.strftime('%Y%m%d')}-{i+1:03d}"
        ET.SubElement(pmt_id, "UETR").text = str(uuid.uuid4())

        amt_el = ET.SubElement(tx_inf, "IntrBkSttlmAmt", Ccy=currency)
        amt_el.text = f"{base_amount:.2f}"
        ET.SubElement(tx_inf, "IntrBkSttlmDt").text = now.strftime("%Y-%m-%d")

        # Instructing Agent
        instg_agt = ET.SubElement(tx_inf, "InstgAgt")
        ET.SubElement(ET.SubElement(instg_agt, "FinInstnId"), "BICFI").text = generate_valid_bic("DE")

        # Instructed Agent
        instd_agt = ET.SubElement(tx_inf, "InstdAgt")
        ET.SubElement(ET.SubElement(instd_agt, "FinInstnId"), "BICFI").text = generate_valid_bic("FR")

    return format_xml(doc)


def generate_camt053(
    currency: str = "USD",
    opening_balance: Decimal = Decimal("100000.00"),
    entries_count: int = 3,
) -> str:
    """Generate ISO 20022 camt.053.001.10 (Bank-To-Customer Statement)."""
    ns = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.10"
    doc = ET.Element("Document", xmlns=ns)
    root = ET.SubElement(doc, "BkToCstmrStmt")

    now = datetime.now(timezone.utc)
    msg_id = f"STMT{now.strftime('%Y%m%d%H%M%S')}"

    grp_hdr = ET.SubElement(root, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = msg_id
    ET.SubElement(grp_hdr, "CreDtTm").text = now.isoformat()

    stmt = ET.SubElement(root, "Stmt")
    ET.SubElement(stmt, "Id").text = f"STMT-{now.strftime('%Y%m%d')}-01"
    ET.SubElement(stmt, "CreDtTm").text = now.isoformat()

    # Account
    acct = ET.SubElement(stmt, "Acct")
    ET.SubElement(ET.SubElement(acct, "Id"), "IBAN").text = generate_valid_iban("DE")
    ET.SubElement(acct, "Ccy").text = currency

    # Opening Balance (OPBD)
    bal_open = ET.SubElement(stmt, "Bal")
    tp_open = ET.SubElement(bal_open, "Tp")
    cd_open = ET.SubElement(tp_open, "CdOrPrtry")
    ET.SubElement(cd_open, "Cd").text = "OPBD"
    amt_open = ET.SubElement(bal_open, "Amt", Ccy=currency)
    amt_open.text = f"{opening_balance:.2f}"
    ET.SubElement(bal_open, "CdtDbtInd").text = "CRDT"
    dt_open = ET.SubElement(bal_open, "Dt")
    ET.SubElement(dt_open, "Dt").text = now.strftime("%Y-%m-%d")

    current_balance = opening_balance

    # Entries
    for i in range(entries_count):
        entry_amt = Decimal("1500.00") * (i + 1)
        is_credit = (i % 2 == 0)
        indicator = "CRDT" if is_credit else "DBIT"
        if is_credit:
            current_balance += entry_amt
        else:
            current_balance -= entry_amt

        ntry = ET.SubElement(stmt, "Ntry")
        amt_el = ET.SubElement(ntry, "Amt", Ccy=currency)
        amt_el.text = f"{entry_amt:.2f}"
        ET.SubElement(ntry, "CdtDbtInd").text = indicator
        ET.SubElement(ntry, "Sts").text = "BOOK"
        bk_dt = ET.SubElement(ntry, "BookgDt")
        ET.SubElement(bk_dt, "Dt").text = now.strftime("%Y-%m-%d")
        ET.SubElement(ntry, "AcctSvcrRef").text = f"REF-{now.strftime('%Y%m%d')}-{i+1:03d}"

    # Closing Balance (CLBD)
    bal_close = ET.SubElement(stmt, "Bal")
    tp_close = ET.SubElement(bal_close, "Tp")
    cd_close = ET.SubElement(tp_close, "CdOrPrtry")
    ET.SubElement(cd_close, "Cd").text = "CLBD"
    amt_close = ET.SubElement(bal_close, "Amt", Ccy=currency)
    amt_close.text = f"{current_balance:.2f}"
    ET.SubElement(bal_close, "CdtDbtInd").text = "CRDT" if current_balance >= 0 else "DBIT"
    dt_close = ET.SubElement(bal_close, "Dt")
    ET.SubElement(dt_close, "Dt").text = now.strftime("%Y-%m-%d")

    return format_xml(doc)


def generate_pain001(
    count: int = 2,
    currency: str = "USD",
    base_amount: Decimal = Decimal("3200.00"),
) -> str:
    """Generate ISO 20022 pain.001.001.11 (Customer Credit Transfer Initiation)."""
    ns = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.11"
    doc = ET.Element("Document", xmlns=ns)
    root = ET.SubElement(doc, "CstmrCdtTrfInitn")

    now = datetime.now(timezone.utc)
    msg_id = f"PAIN{now.strftime('%Y%m%d%H%M%S')}"

    total_sum = base_amount * count

    # Group Header
    grp_hdr = ET.SubElement(root, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = msg_id
    ET.SubElement(grp_hdr, "CreDtTm").text = now.isoformat()
    ET.SubElement(grp_hdr, "NbOfTxs").text = str(count)
    ET.SubElement(grp_hdr, "CtrlSum").text = f"{total_sum:.2f}"
    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    ET.SubElement(initg_pty, "Nm").text = "Corporate Treasury Holdings LLC"

    # Payment Information
    pmt_inf = ET.SubElement(root, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = f"PMTINF-{now.strftime('%Y%m%d')}-01"
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, "NbOfTxs").text = str(count)
    ET.SubElement(pmt_inf, "CtrlSum").text = f"{total_sum:.2f}"

    # Debtor
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = "Corporate Treasury Holdings LLC"
    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    ET.SubElement(ET.SubElement(dbtr_acct, "Id"), "IBAN").text = generate_valid_iban("DE")

    for i in range(count):
        tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
        pmt_id = ET.SubElement(tx_inf, "PmtId")
        ET.SubElement(pmt_id, "EndToEndId").text = f"CORP-PAY-{now.strftime('%Y%m%d')}-{i+1:04d}"

        amt_el = ET.SubElement(tx_inf, "Amt")
        instd = ET.SubElement(amt_el, "InstdAmt", Ccy=currency)
        instd.text = f"{base_amount:.2f}"

        cdtr = ET.SubElement(tx_inf, "Cdtr")
        ET.SubElement(cdtr, "Nm").text = f"Vendor Partner #{i+1}"
        cdtr_acct = ET.SubElement(tx_inf, "CdtrAcct")
        ET.SubElement(ET.SubElement(cdtr_acct, "Id"), "IBAN").text = generate_valid_iban("GB")

    return format_xml(doc)
