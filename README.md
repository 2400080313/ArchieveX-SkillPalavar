# 📦 ArchiveX: Intelligent Amazon S3 Archive & Lifecycle Decision Support Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io)
[![AWS-SDK](https://img.shields.io/badge/AWS%20Boto3-S3%20%7C%20STS-232F3E.svg)](https://aws.amazon.com/sdk-for-python/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

> **AWS Storage Hackathon Edition**  
> *"ArchiveX does not replace Amazon S3's native storage optimization capabilities. It makes them easier to understand, monitor, and operationalize through an intelligent decision-support layer."*

---

## 🧭 The Hackathon Narrative & Positioning

```
DATA GENERATION
       ↓
  S3 STORAGE
       ↓
OBJECT ANALYSIS
       ↓
ARCHIVE INTELLIGENCE (ArchiveX Scoring Engine)
       ↓
RECOMMENDATION (Context-Aware Tier Targets)
       ↓
LIFECYCLE / INTELLIGENT-TIERING (Guardrails & IaC)
       ↓
OPTIMIZED STORAGE (Glacier Deep Archive / INT)
       ↓
COST VISIBILITY (Break-Even & ROI Tracking)
```

Modern cloud data lakes and enterprise applications generate petabytes of objects into Amazon S3. While AWS provides industry-leading storage classes (S3 Intelligent-Tiering, Glacier Flexible, Glacier Deep Archive), teams often leave terabytes idling in expensive S3 Standard due to:
1. **Fear of retrieval penalties:** Uncertainty about retrieval latency and fees.
2. **Small-object fee traps:** Transitioning objects < 128 KB to Glacier or Standard-IA can increase costs due to minimum billable capacity and per-request transition fees.
3. **Operational inertia:** Writing and safely validating multi-stage S3 Lifecycle XML/JSON policies requires deep expertise.

**ArchiveX bridges this gap.** It acts as a safety-first decision-support layer that analyzes object age, size distributions, prefix semantics, and tags to recommend the optimal S3 storage class, calculate break-even timelines, enforce small-object guardrails, and generate deployment-ready Terraform and JSON policies.

---

## ✨ Key Features & Capabilities

- **📊 Executive Storage & Financial Dashboard:** High-level KPIs, storage class distributions, inactivity aging tiers, and aggregate annual ROI metrics.
- **🎯 Multi-Factor Archive Readiness Scoring (0–100):** Evaluates object age (35%), payload size (25%), semantic patterns (20%), existing tier (10%), and compliance tags (10%).
- **💰 Interactive Cost & ROI Simulator:** Real-time financial modeling factoring in one-time transition request fees, monthly monitoring fees ($0.0025/1k), and retrieval sensitivity analysis with break-even horizons.
- **⚙️ S3 Lifecycle Policy Builder & Dry-Run Inspector:** Define prefix rules, enforce 128 KB guardrails, and simulate the exact impact against bucket contents before deployment. Exports to AWS CLI JSON, S3 API XML, and Terraform HCL.
- **🧠 S3 Intelligent-Tiering Analytics:** Deep-dive into tier distribution (Frequent, Infrequent, Archive Instant, Deep Archive), small-object density warnings, and net monthly savings.
- **🔍 Granular S3 Bucket Explorer:** Multi-facet filtering by age, size, storage class, and readiness score, with full object metadata inspection.
- **💬 ArchiveX Copilot / Rule-based Archive Assistant:** Natural-language explanation engine providing transparent, deterministic architectural rationales (e.g., *"Why should I archive this backup?"*). Supports optional LLM augmentation via Google Gemini / OpenAI.
- **🛡️ Enterprise Security & Guardrails:** Zero hardcoded credentials, read-only default operations, and mandatory two-factor explicit confirmation before applying changes to live AWS buckets.
- **🚀 Zero-Configuration Demo Mode:** Instantly testable without AWS credentials across 5 enterprise bucket workloads (PostgreSQL backups, FinTech compliance logs, 4K media assets, CDN web assets, IoT telemetry).

---

## 📂 Project Architecture

```
archivex/
├── .env.example              # Environment variables template (AWS keys, optional LLM)
├── .gitignore                # Production git ignore rules
├── requirements.txt          # Python dependencies
├── README.md                 # Hackathon documentation and architecture guide
├── run.py                    # Convenience one-click launcher
├── app.py                    # Main Streamlit application entry point
├── config.py                 # AWS S3 pricing constants, heuristics, and scoring weights
├── core/
│   ├── __init__.py           # Package exports
│   ├── aws_client.py         # Safe Boto3 client with dry-run guards and STS validation
│   ├── demo_data.py          # Realistic synthetic enterprise bucket dataset generator
│   ├── scoring.py            # 5-factor Archive Readiness scoring engine (0-100)
│   ├── cost_engine.py        # AWS S3 storage, retrieval, and transition cost engine
│   ├── lifecycle_gen.py      # S3 Lifecycle generator (JSON, XML, Terraform) & dry-run
│   ├── intelligent_tiering.py# S3 Intelligent-Tiering suitability & fee analyzer
│   └── copilot.py            # Rule-based Archive Assistant & LLM Copilot connector
├── ui/
│   ├── __init__.py           # UI exports
│   ├── styles.py             # Custom CSS, AWS cloud console aesthetic, theme badges
│   ├── components.py         # Reusable KPI cards, class badges, score indicators
│   ├── dashboard_view.py     # Executive dashboard view
│   ├── explorer_view.py      # Bucket explorer and object inspector view
│   ├── recommendations_view.py# Actionable tier recommendation review view
│   ├── simulator_view.py     # Interactive cost and ROI simulator view
│   ├── lifecycle_view.py     # Lifecycle builder & dry-run simulation view
│   ├── it_view.py            # Intelligent-Tiering deep dive view
│   ├── copilot_view.py       # Copilot chat and explanation interface
│   └── settings_view.py      # AWS authentication, bucket selection, mode toggle
└── tests/
    ├── __init__.py
    ├── test_scoring.py       # Tests for scoring thresholds & 128KB guardrail
    ├── test_cost_engine.py   # Tests for pricing calculations, break-even & ROI
    ├── test_lifecycle_gen.py # Tests for JSON/XML generation and dry-run simulation
    ├── test_copilot.py       # Tests for deterministic natural-language responses
    └── test_demo_data.py     # Tests for demo dataset integrity
```

---

## 🚀 Quickstart: How to Run ArchiveX

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone or navigate to the project directory
cd archivex

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application
You can run ArchiveX using the convenience launcher or directly with Streamlit:
```bash
# Option A: Convenience launcher
python run.py

# Option B: Direct Streamlit command
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### 4. Run the Test Suite
```bash
pytest -v tests/
```
All 17 unit tests should pass with 100% green status.

---

## 🔌 AWS Setup & Live Connection

ArchiveX starts in **Demo Mode** by default. To connect to your live AWS account:

### Step 1: Minimum AWS IAM Policy
Create an IAM user or role with the following least-privilege policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ArchiveXReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetLifecycleConfiguration",
        "s3:GetObjectTagging"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ArchiveXLifecycleWriteOptional",
      "Effect": "Allow",
      "Action": [
        "s3:PutLifecycleConfiguration"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name"
    }
  ]
}
```

### Step 2: Configure Credentials
You have three options:
1. **Via the UI:** Navigate to **Settings & AWS Setup**, toggle off Demo Mode, enter your `AWS Access Key ID`, `AWS Secret Access Key`, and `Region`, then click **Test AWS Connection**.
2. **Via `.env` file:** Copy `.env.example` to `.env` and fill in your keys.
3. **Via Standard AWS CLI:** If you have run `aws configure`, ArchiveX automatically discovers credentials from `~/.aws/credentials`.

---

## 🎬 Hackathon Demo Flow (5-Minute Walkthrough)

Follow this sequence to present ArchiveX to hackathon judges:

1. **The Problem & Positioning (1 min):**
   - Open the **Executive Dashboard**.
   - Point out the story pipeline: `DATA GENERATION -> S3 STORAGE -> OBJECT ANALYSIS -> ARCHIVE INTELLIGENCE -> RECOMMENDATION -> LIFECYCLE -> OPTIMIZATION -> COST VISIBILITY`.
   - Quote: *"ArchiveX does not replace S3's native capabilities; it makes them transparent and actionable."*
   - Show the 5 diverse enterprise bucket workloads (Backups, Compliance, Media, Web, IoT).

2. **Archive Readiness Scoring & Explorer (1 min):**
   - Switch to **Bucket Explorer**.
   - Show how ArchiveX scores each object (0–100) combining age, size, and prefix patterns.
   - Inspect a 400+ day database dump: note how ArchiveX flags it for **Glacier Deep Archive** saving up to 95.7%.
   - Filter by **Small Objects (< 128 KB)**: demonstrate the **128 KB Guardrail** preventing cost-inefficient transitions.

3. **Financial Modeling & ROI Simulator (1 min):**
   - Navigate to **Cost & ROI Simulator**.
   - Move the storage slider to 50 TB and demonstrate real-time break-even calculations.
   - Adjust the **Monthly Retrieval %**: show the instant warning if retrieval fees outpace storage savings.

4. **S3 Intelligent-Tiering Deep-Dive (45 sec):**
   - Navigate to **S3 Intelligent-Tiering**.
   - Highlight the **$0.0025/1k monitoring fee** calculation and the automatic simulation across Frequent, Infrequent, Archive Instant, and Deep Archive tiers.

5. **S3 Lifecycle Policy Builder & Dry Run (45 sec):**
   - Open **S3 Lifecycle Builder**.
   - Show the interactive rule designer with the **128 KB guardrail** enabled.
   - Run the **Dry-Run Simulation**: point out how many objects would transition and how many small objects are protected.
   - Switch to **Export Infrastructure Code**: view the production **Terraform HCL** and **AWS JSON** policy ready for CI/CD.

6. **ArchiveX Copilot (30 sec):**
   - Navigate to **ArchiveX Copilot**.
   - Click the prompt: *"Why should I archive this backup?"*
   - Demonstrate the deterministic, transparent response:
     > *"Because it is 412 days old, currently stored in S3 Standard, and its available metadata indicates it is a strong long-term archive candidate. Access frequency is unavailable, so this recommendation should be reviewed before applying changes."*
   - Note the **"Rule-based Archive Assistant"** badge guaranteeing zero hallucination.

---

## 📋 Hackathon Quality Checklist Verification

- [x] **Application starts:** Launches cleanly via `python run.py` and `streamlit run app.py`
- [x] **No import errors:** Zero unresolved dependencies or syntax issues
- [x] **Dashboard loads:** Full executive KPI cards and dual-row distribution charts
- [x] **Demo Mode works without AWS:** 5 comprehensive enterprise workloads ready out-of-the-box
- [x] **Demo data loads:** 1,000+ realistic objects with dates, sizes, classes, and tags
- [x] **Charts work:** Plotly interactive donut, bar, and cumulative time-series charts
- [x] **Archive scoring works:** 5-factor scoring engine (0-100)
- [x] **Recommendations work:** Precise mapping to Deep Archive, Flexible, Instant, INT, or Keep Standard
- [x] **Cost simulator works:** Sliders, break-even days, retrieval sensitivity, and ROI projections
- [x] **Lifecycle page works:** Rule designer, dry-run impact assessment, and Terraform/JSON/XML export
- [x] **Intelligent-Tiering page works:** Suitability scoring, 128KB guardrail metrics, monitoring fees
- [x] **Bucket Explorer works:** Granular search, storage class filters, and metadata inspector
- [x] **Search works:** Live key, prefix, and extension matching
- [x] **Filters work:** Multi-select classes, age slider, score slider, payload size filter
- [x] **Explanation panel works:** ArchiveX Copilot labeled "Rule-based Archive Assistant"
- [x] **Settings work:** Mode toggles, credentials input, region selector
- [x] **AWS connection test works:** Safe STS verification with clear error handling
- [x] **AWS S3 read operations work:** Safe listing of buckets and objects via Boto3
- [x] **AWS modifications require confirmation:** Mandatory two-step confirmation before applying lifecycle rules
- [x] **No credentials hardcoded:** Read via environment variables, `.env`, or runtime state
- [x] **Error handling works:** Graceful fallbacks on AWS exceptions and empty buckets
- [x] **README exists:** Comprehensive architecture, demo flow, and run guide
- [x] **requirements.txt exists:** Fully pinned dependencies
- [x] **.env.example exists:** Clean configuration template
- [x] **.gitignore exists:** Standard Python/AWS exclusion rules
- [x] **Basic tests exist:** 17 unit tests passing across all core modules

---

## ⚖️ Current Limitations & Production Roadmap

1. **S3 Object Access Metrics:** S3 Storage Lens and CloudWatch Request metrics can be integrated via AWS Athena / S3 Inventory reports to ingest real access frequency histograms alongside LastModified timestamps.
2. **Multi-Bucket Batch Lifecycle Application:** Currently applies lifecycle policies bucket-by-bucket; roadmap includes organization-wide AWS Organizations / AWS Control Tower deployment.
3. **Automated Small-Object Compaction:** Future release will introduce an AWS Lambda / AWS Glue crawler to automatically bundle small objects (<128 KB) into compressed `.parquet` or `.tar.gz` bundles before cold tiering.

---

## 📜 License
Apache License 2.0. Built for the AWS Storage Innovation Hackathon.
