# AI Pipeline Refactoring (Lab Submission)

This repository contains refactored production AI pipelines from monolithic implementations into modular, defensively engineered Python packages.

- **Path 1 (`path1/`)**: AI Product Listing Generator — vision pipeline split into modular configuration, data loading, prompt building, and API client layers.
- **Path 2 (`path2/`)**: LangChain Meal Planner — structured output pipeline with schema normalization, defensive parsing, and stratified error handling.

---

## 📁 Repository Structure

```text
LAB-Refactoring/
├── .env.example
├── README.md
├── requirements.txt
├── lab_summary.md
├── lab_proof.md
├── before_after_comparison.md
├── refactoring_checklist.md
├── testing_helper_finctions.ipynb
│
├── path1/                          # Product Listing Generator
├   ├── data
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   ├── data_loader.py
│   ├── image_utils.py
│   ├── prompt_builder.py
│   ├── api_client.py
│   └── product_listing_generator.py
│   └── product_listing_generator_original.py
│
└── path2/                          # Meal Planner
    ├── __init__.py
    ├── meal_planner_config.py
    ├── models.py
    ├── prompts.py
    ├── json_utils.py
    ├── email_utils.py
    ├── meal_plan_generator.py
    ├── dataset_evaluation.py
    ├── evaluators.py
    ├── meal_planner.ipynb
    ├── meal_planner_refactored.ipynb
    └── app.py
```

## 🚀 Quick Start & Environment Setup
1. Prerequisites
Ensure you have Python 3.10+ installed.

2. Clone Repository & Setup Virtual Environment
3. Install Dependencies
`pip install --upgrade pip`
`pip install -r requirements.txt`

4. Configure Environment Variables
Copy .env.example to create your local .env file:
`cp .env.example .env`

## Running the Project

### Running Path 1: Product Listing Generator
Execute Path 1 as a module from the repository root:
`python -m path1.product_listing_generator`

### Running Path 2: Meal Planner
jupyter notebook meal_planner.ipynb

