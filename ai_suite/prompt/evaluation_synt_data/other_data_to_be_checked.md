

## Synthetic Data Examples

Below are three use cases showcasing how our solution can be applied. For each, we provide synthetic CSV data representing document-level statistics and field-level statistics.

### Use Case 1: Invoice Data Extraction

*Evaluation Focus:*  
Ensuring accurate extraction of invoice details (e.g., invoice number, date, vendor, amount, and tax) is crucial for financial accuracy and compliance. This evaluation provides quick insights to scale and optimize LLM-based extraction processes in the finance sector.

**Document-Level Stats (CSV)**
```csv
document,total,correct,missing,accuracy
data\invoices\invoice_20250101.json,30,27,3,90.0
data\invoices\invoice_20250102.json,30,25,5,83.33
data\invoices\invoice_20250103.json,30,28,2,93.33
```

**Field-Level Stats (CSV)**
```csv
field,total,correct,missing,accuracy
invoice_number,30,30,0,100.0
invoice_date,30,29,1,96.67
vendor_name,30,28,2,93.33
amount,30,27,3,90.0
tax,30,26,4,86.67
```

### Use Case 2: Legal Document Analysis

*Evaluation Focus:*  
Extracting key clauses and metadata (e.g., parties involved, effective dates, termination clauses, confidentiality provisions) from contracts is essential for legal compliance and risk management. Our evaluation helps legal professionals compare different extraction settings and verify critical details automatically.

**Document-Level Stats (CSV)**
```csv
document,total,correct,missing,accuracy
data\legal\contract_A.json,20,18,2,90.0
data\legal\contract_B.json,20,17,3,85.0
data\legal\contract_C.json,20,19,1,95.0
```

**Field-Level Stats (CSV)**
```csv
field,total,correct,missing,accuracy
party_names,20,20,0,100.0
effective_date,20,18,2,90.0
termination_clause,20,17,3,85.0
confidentiality,20,19,1,95.0
```

### Use Case 3: RAG Application Compliance Check

*Evaluation Focus:*  
Validating the extraction of key compliance elements—such as response content, supporting references, compliance flags, and metadata—is vital for ensuring that a Retrieval Augmented Generation (RAG) system meets regulatory and quality standards. This evaluation is critical for rapidly iterating on prompt designs and ensuring regulatory compliance.

**Document-Level Stats (CSV)**
```csv
document,total,correct,missing,accuracy
data\rag\compliance_20250101.json,40,36,4,90.0
data\rag\compliance_20250102.json,40,34,6,85.0
data\rag\compliance_20250103.json,40,38,2,95.0
```

**Field-Level Stats (CSV)**
```csv
field,total,correct,missing,accuracy
response_text,40,38,2,95.0
supporting_references,40,36,4,90.0
compliance_flags,40,37,3,92.5
metadata,40,39,1,97.5
```

---

O1
---
### **Use Case 2: Real Estate Listings**

**Short Description**:  
A real estate platform needs to verify that automated property listings (sourced from multiple agencies) match the official listings. Fields like “Property Address,” “Listing Price,” and “Number of Bedrooms” are compared to ensure data quality.

**Document-Level Results (CSV)**

<details>
<summary><strong>document_stats_usecase2.csv</strong></summary>

```csv
document,total,correct,missing,accuracy
data/test/auto_scraped/api1/listing_1001.json,50,45,5,90.0
data/test/auto_scraped/api1/listing_1002.json,45,35,10,77.8
data/test/auto_scraped/api2/listing_1003.json,40,32,8,80.0
data/test/manual_extraction/listing_1004.json,60,54,6,90.0
```
</details>

**Field-Level Results (CSV)**

<details>
<summary><strong>field_stats_usecase2.csv</strong></summary>

```csv
field,total,correct,missing,accuracy
property_address,10,9,1,90.0
listing_price,10,7,3,70.0
number_of_bedrooms,10,10,0,100.0
number_of_bathrooms,10,8,2,80.0
square_footage,10,7,3,70.0
listing_agent,10,9,1,90.0
property_type,10,9,1,90.0
images_count,10,5,5,50.0
has_garage,10,10,0,100.0
additional_notes,10,8,2,80.0
```
</details>

---

### **Use Case 3: Healthcare Insurance Claims**

**Short Description**:  
A healthcare administrator reviews patient insurance claims to confirm accuracy. Fields such as “Patient ID,” “Diagnosis Codes,” and “Claim Amount” are critical for billing and compliance. The system helps ensure no important detail is overlooked.

**Document-Level Results (CSV)**

<details>
<summary><strong>document_stats_usecase3.csv</strong></summary>

```csv
document,total,correct,missing,accuracy
data/test/auto_scraped/claims/run1_claim_001.json,35,30,5,85.7
data/test/auto_scraped/claims/run1_claim_002.json,40,34,6,85.0
data/test/auto_scraped/claims/run2_claim_003.json,30,25,5,83.3
data/test/manual_extraction/claims/claim_004.json,50,47,3,94.0
```
</details>

**Field-Level Results (CSV)**

<details>
<summary><strong>field_stats_usecase3.csv</strong></summary>

```csv
field,total,correct,missing,accuracy
patient_id,8,8,0,100.0
insurance_provider,8,6,2,75.0
diagnosis_codes,8,7,1,87.5
procedure_codes,8,5,3,62.5
claim_amount,8,6,2,75.0
claim_approval_status,8,7,1,87.5
co_pay_amount,8,6,2,75.0
additional_notes,8,7,1,87.5
```
</details>

In this example, “diagnosis_codes” and “claim_approval_status” typically have high accuracy, while “procedure_codes” might be more error-prone due to more complex or variable naming schemes.

### **Use Case 2: HR & Recruiting – Job Postings**

#### Document-Level Statistics

**Filename:** `document_stats_jobs.csv`
```csv
document,total,correct,missing,accuracy
data/test/auto_scraped/jobs/posting_101.json,15,14,1,93.3
data/test/auto_scraped/jobs/posting_102.json,15,12,3,80.0
data/test/auto_scraped/jobs/posting_103.json,15,13,2,86.7
data/test/manual/jobs/posting_104.json,18,16,2,88.9
data/test/manual/jobs/posting_105.json,18,17,1,94.4
data/test/auto_scraped/jobs/posting_106.json,15,11,4,73.3
```

#### Field-Level Statistics

**Filename:** `field_stats_jobs.csv`
```csv
field,total,correct,missing,accuracy
job_title,12,12,0,100.0
company_name,12,11,1,91.7
location,12,10,2,83.3
salary_range,12,9,3,75.0
job_type,12,9,3,75.0
responsibilities,12,8,4,66.7
requirements,12,10,2,83.3
benefits,12,7,5,58.3
posted_date,12,11,1,91.7
closing_date,12,10,2,83.3
```
The **“benefits”** field has lower accuracy (58.3%), indicating potential complexity or variability in how benefits are listed.

---

### **Use Case 3: Healthcare – Insurance Claims**

#### Document-Level Statistics

**Filename:** `document_stats_healthcare.csv`
```csv
document,total,correct,missing,accuracy
data/test/auto_scraped/claims/claim_001.json,20,18,2,90.0
data/test/auto_scraped/claims/claim_002.json,20,17,3,85.0
data/test/auto_scraped/claims/claim_003.json,20,15,5,75.0
data/test/manual/claims/claim_004.json,25,23,2,92.0
data/test/manual/claims/claim_005.json,25,24,1,96.0
data/test/auto_scraped/claims/claim_006.json,20,19,1,95.0
```

#### Field-Level Statistics

**Filename:** `field_stats_healthcare.csv`
```csv
field,total,correct,missing,accuracy
patient_id,15,15,0,100.0
insurance_provider,15,13,2,86.7
diagnosis_codes,15,12,3,80.0
procedure_codes,15,11,4,73.3
claim_amount,15,13,2,86.7
claim_approval_status,15,14,1,93.3
hospital_name,15,13,2,86.7
admission_date,15,14,1,93.3
discharge_date,15,13,2,86.7
co_pay_amount,15,12,3,80.0
notes,15,10,5,66.7
```
Low accuracy for **“notes”** (66.7%) can indicate missing or incomplete textual details.

---