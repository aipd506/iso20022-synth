"""Pure-Python ISO 7064 MOD-97 IBAN and ISO 9362 BIC generation and validation."""

import random
import re
from typing import Tuple


def calculate_iban_checksum(country_code: str, bban: str) -> str:
    """Calculate 2-digit check digits for a given country code and BBAN using ISO 7064 MOD-97."""
    rearranged = bban + country_code + "00"
    digits = ""
    for ch in rearranged:
        if ch.isdigit():
            digits += ch
        elif ch.isalpha():
            digits += str(ord(ch.upper()) - 55)
        else:
            raise ValueError(f"Invalid character in IBAN calculation: {ch}")

    remainder = int(digits) % 97
    check_digits = 98 - remainder
    return f"{check_digits:02d}"


def validate_iban(iban: str) -> Tuple[bool, str]:
    """Validate an IBAN string using the ISO 7064 MOD-97 algorithm."""
    clean = re.sub(r"\s+", "", iban).upper()
    if len(clean) < 5:
        return False, "IBAN too short"
    if not clean[:2].isalpha():
        return False, "First two characters must be country code"
    if not clean[2:4].isdigit():
        return False, "Characters 3 and 4 must be check digits"

    country_code = clean[:2]
    check_digits = clean[2:4]
    bban = clean[4:]

    rearranged = bban + country_code + check_digits
    digits = ""
    for ch in rearranged:
        if ch.isdigit():
            digits += ch
        elif ch.isalpha():
            digits += str(ord(ch) - 55)
        else:
            return False, f"Illegal character in IBAN: {ch}"

    if int(digits) % 97 != 1:
        return False, "MOD-97 checksum failed"

    return True, "Valid"


def generate_valid_iban(country_code: str = "DE") -> str:
    """Generate a mathematically valid synthetic IBAN for testing."""
    country = country_code.upper()
    if country == "DE":
        # Germany: DE + 2 check + 8 bank code + 10 account num = 22 chars
        bank_code = f"{random.randint(10000000, 99999999):08d}"
        account_num = f"{random.randint(1000000000, 9999999999):010d}"
        bban = bank_code + account_num
    elif country == "GB":
        # UK: GB + 2 check + 4 bank code + 6 sort code + 8 account num = 22 chars
        bank_code = "BARC"
        sort_code = f"{random.randint(100000, 999999):06d}"
        account_num = f"{random.randint(10000000, 99999999):08d}"
        bban = bank_code + sort_code + account_num
    elif country == "FR":
        # France: FR + 2 check + 5 bank + 5 branch + 11 account + 2 national check = 27 chars
        bank = f"{random.randint(10000, 99999):05d}"
        branch = f"{random.randint(10000, 99999):05d}"
        acc = f"{random.randint(10000000000, 99999999999):011d}"
        bban = bank + branch + acc + "00"
    else:
        # Generic 16-char BBAN
        bban = "".join([str(random.randint(0, 9)) for _ in range(16)])

    check = calculate_iban_checksum(country, bban)
    return f"{country}{check}{bban}"


def generate_valid_bic(country_code: str = "DE") -> str:
    """Generate a valid synthetic ISO 9362 BIC8 or BIC11."""
    banks = ["DEUT", "CHAS", "CITI", "BNPA", "HSBC", "BARC", "SANB", "INGB"]
    chosen = random.choice(banks)
    location = "2X"
    branch = "XXX"
    return f"{chosen}{country_code.upper()}{location}{branch}"
