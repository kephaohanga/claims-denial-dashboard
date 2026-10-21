import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

# Set a deterministic seed so the synthetic data is reproducible.
random.seed(42)

# Build paths relative to this script.
BASE_DIR = Path(__file__).resolve().parent
REFERENCE_FILE = BASE_DIR / "data" / "reference-data.json"
OUTPUT_FILE = BASE_DIR / "claims_dataset.csv"

# Clinical reference pairs that will be used to seed ICD-10/CPT combinations.
with REFERENCE_FILE.open("r", encoding="utf-8") as fh:
    reference_pairs = json.load(fh)

valid_pairs = {(item["icd10"], item["cpt"]) for item in reference_pairs}
procedure_lookup = {item["cpt"]: item["procedure"] for item in reference_pairs}

# Configuration for the synthetic dataset.
ROW_COUNT = 600
TARGET_DENIALS = 60  # 10% overall denial rate
payers = ["Aetna", "BCBS", "Medicare", "UnitedHealth", "Cigna"]
providers = [
    "Northwell Billing Center",
    "Harborview Medical Group",
    "Summit Health Partners",
    "Lakeview Specialty Care",
    "Pine Ridge Outpatient",
    "Cedar Valley Physicians"
]

denial_reason_map = {
    "CO-11": "Diagnosis inconsistent with procedure",
    "CO-50": "Not medically necessary",
    "CO-197": "Missing prior authorization",
    "CO-18": "Duplicate claim",
    "CO-29": "Timely filing limit expired",
    "CO-16": "Coding error or missing information",
}

# Create a reason pool that approximates the requested denial mix.
# This gives us 60 denied claims with the desired coverage:
# - 40% medical necessity / mismatch (CO-11 + CO-50)
# - 21.7% prior authorization
# - 15% duplicate
# - 11.7% coding error
# - 11.7% timely filing
reason_pool = (
    ["CO-11"] * 12 +
    ["CO-50"] * 12 +
    ["CO-197"] * 13 +
    ["CO-18"] * 9 +
    ["CO-16"] * 7 +
    ["CO-29"] * 7
)
random.shuffle(reason_pool)

# Generate claim rows.
rows = []
today = date.today()
start_date = today - timedelta(days=365)

for idx in range(1, ROW_COUNT + 1):
    reference = random.choice(reference_pairs)
    icd10_code = reference["icd10"]
    cpt_code = reference["cpt"]
    procedure_name = reference["procedure"]

    # Random but realistic payer/provider assignment.
    payer = random.choice(payers)
    provider = random.choice(providers)

    # For CO-11 denials, force a genuine ICD/CPT mismatch that does not appear
    # in the reference data. Other denial reasons keep a valid pairing.
    if idx <= TARGET_DENIALS and reason_pool[idx - 1] == "CO-11":
        for _ in range(200):
            candidate_icd = random.choice(reference_pairs)["icd10"]
            candidate_cpt = random.choice(reference_pairs)["cpt"]
            if (candidate_icd, candidate_cpt) not in valid_pairs:
                icd10_code = candidate_icd
                cpt_code = candidate_cpt
                procedure_name = procedure_lookup[candidate_cpt]
                break

    # For CO-16 denials, simulate a genuine coding error rather than reusing a
    # valid reference pairing. When the correct CPT carries an -LT/-RT
    # modifier, flip it to the opposite side (wrong-side coding error). When
    # there's no laterality to flip (bilateral -50 codes, or codes with no
    # modifier at all), swap in a CPT code from a different reference row so
    # the resulting icd10/cpt pairing is not a valid combination.
    if idx <= TARGET_DENIALS and reason_pool[idx - 1] == "CO-16":
        if "-LT" in cpt_code:
            cpt_code = cpt_code.replace("-LT", "-RT")
        elif "-RT" in cpt_code:
            cpt_code = cpt_code.replace("-RT", "-LT")
        else:
            for _ in range(200):
                candidate_cpt = random.choice(reference_pairs)["cpt"]
                if candidate_cpt != cpt_code and (icd10_code, candidate_cpt) not in valid_pairs:
                    cpt_code = candidate_cpt
                    procedure_name = procedure_lookup[candidate_cpt]
                    break

    # Create a realistic billed amount based on CPT/procedure complexity.
    # The specific ranges are approximate and can be refined later.
    base_amount = {
        "CT of the head without contrast": 450,
        "Repair of incarcerated ventral hernia, partial omentectomy": 5200,
        "Open left inguinal hernia repair with mesh (PHSL)": 4800,
        "Tonsillectomy (age >12 yrs)": 1800,
        "Repair of incarcerated left inguinal hernia with mesh (PHSL)": 5000,
        "Laparoscopic cholecystectomy": 4100,
        "Right total knee arthroplasty": 13800,
        "Left clavicle ORIF with fluoroscopy": 3600,
        "Left knee arthroscopic lateral meniscal repair": 3200,
        "ORIF right wrist": 4200,
        "Repair of left quadriceps - left lower extremity": 6500,
        "Insertion of implantable loop recorder": 2400,
        "Thrombectomy of the axillary and brachial arteries": 7200,
        "Popliteal to dorsalis pedis bypass graft using saphenous vein": 9800,
        "Left femur intramedullary nailing (displaced comminuted left femoral shaft fracture)": 12500,
        "Locking intramedullary rod fixation - fractured right tibia; Stryker": 11000,
        "Bilateral total knee arthroplasty": 16500,
        "Closed reduction of dislocated left shoulder": 2200,
        "Left knee exam under anesthesia; arthroscopy; ACL reconstruction": 7800,
        "Closed reduction and pin fixation of left fifth metacarpal base fracture": 2600,
        "Right total hip arthroplasty": 14500,
        "Right knee arthroscopy with trimming/debridement": 2200,
        "Open amputation of right third toe": 3100,
        "Removal of Knowles pins x3, right hip": 2600,
    }.get(procedure_name, 3000)

    billed_amount = round(
        random.uniform(base_amount * 0.85, base_amount * 1.15),
        2
    )

    # Decide whether the claim is denied.
    if idx <= TARGET_DENIALS:
        status = "Denied"
        denial_code = reason_pool[idx - 1]
        denial_desc = denial_reason_map[denial_code]
        paid_amount = 0.00
    else:
        status = "Paid"
        denial_code = ""
        denial_desc = ""

        # Paid claims are often paid in full, but a small share is partially paid.
        if random.random() < 0.15:
            paid_amount = round(billed_amount * random.uniform(0.55, 0.9), 2)
        else:
            paid_amount = round(billed_amount, 2)

    # Spread claims across the last 12 months.
    submission_date = start_date + timedelta(days=random.randint(0, 365))

    rows.append({
        "claim_id": f"CLM-{idx:05d}",
        "patient_id": f"PT-{idx:04d}",
        "payer": payer,
        "provider": provider,
        "icd10_code": icd10_code,
        "cpt_code": cpt_code,
        "billed_amount": f"{billed_amount:.2f}",
        "paid_amount": f"{paid_amount:.2f}",
        "status": status,
        "denial_reason_code": denial_code,
        "denial_reason_desc": denial_desc,
        "submission_date": submission_date.strftime("%Y-%m-%d")
    })

# Write the CSV.
fieldnames = [
    "claim_id",
    "patient_id",
    "payer",
    "provider",
    "icd10_code",
    "cpt_code",
    "billed_amount",
    "paid_amount",
    "status",
    "denial_reason_code",
    "denial_reason_desc",
    "submission_date"
]

with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created {len(rows)} records at {OUTPUT_FILE}")
