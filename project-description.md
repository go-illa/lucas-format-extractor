# Lucas Format Extractor Project Description

An automated ETL pipeline that transforms raw Excel files into a predefined schema using an LLM-driven approach. It's designed for serverless deployment as an AWS Lambda function.
The pipeline now includes database-driven mapping for client codes (e.g., SKU, Location) to internal identifiers, generates output files with dynamic names based on the input file, and features enhanced data cleaning and robust handling of diverse input file names.

## Feature to Function/Module Mapping

| Feature | Module | Function(s) |
| :--- | :--- | :--- |
| **End-to-End Orchestration** | `main.py` | `process_client_file()` |
| **Local Execution & Dynamic Naming** | `main.py` | `if __name__ == "__main__"` |
| **Lambda Execution Entrypoint**| `lambda_function.py` | `lambda_handler()` |
| **LLM API Handling (with fallback)**| `etl/llm_client.py`| `create_chat_completion()` |
| **1. Data Extraction** | `etl/extractor.py` | `extract_main_table()` (Enhanced empty/summary row handling) |
| **2. Transformation Planning** | `etl/planner.py` | `select_action_with_llm()` |
| **3. Data Transformation & Mapping** | `etl/actions.py` | `apply_direct_mapping()`, `unpivot_wide_to_long()`|
| **4. Database Code Retrieval**| `etl/mapping.py` | `get_sku_mapping()`, `get_location_mapping()`|
| **Dependency Management** | `requirements.txt` | `psycopg2-binary` addition |
| **Deployment Packaging** | `build_lambda_package.sh` | (script) |
| **Automated Deployment (CI/CD)**| `.github/workflows/deploy-lambda.yml` | (workflow) |
