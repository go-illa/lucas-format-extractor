# Lucas Format Extractor Project Description

An automated ETL pipeline that transforms raw Excel files into a predefined schema using an LLM-driven approach. It's designed for serverless deployment as an AWS Lambda function.

The pipeline has been refactored for clarity and robustness. It now intelligently iterates through all sheets in a multi-tab Excel file, uses heuristics to validate extracted data, and includes improved error handling in the Lambda function. It also includes database-driven mapping for client codes and generates dynamically named output files.

## Feature to Function/Module Mapping

| Feature | Module | Function(s) |
| :--- | :--- | :--- |
| **Core ETL Orchestration** | `etl/pipeline.py` | `process_client_file()` |
| **Local Execution** | `main.py` | `if __name__ == "__main__"` |
| **Lambda Execution & Error Handling**| `lambda_function.py` | `lambda_handler()` |
| **Multi-Sheet & Heuristic Extraction** | `etl/pipeline.py` | `process_client_file()` loop |
| **LLM API Handling** | `etl/llm_client.py`| `create_chat_completion()` |
| **1. Data Extraction** | `etl/extractor.py` | `extract_main_table()` |
| **2. Transformation Planning** | `etl/planner.py` | `select_action_with_llm()` |
| **3. Data Transformation & Mapping** | `etl/actions.py` | `apply_direct_mapping()`, `unpivot_wide_to_long()`|
| **4. Database Code Retrieval**| `etl/mapping.py` | `get_sku_mapping()`, `get_location_mapping()`|
| **Dependency Management** | `requirements.txt` | `psycopg2-binary` addition |
| **Deployment Packaging** | `build_lambda_package.sh` | (script) |
| **Automated Deployment (CI/CD)**| `.github/workflows/deploy-lambda.yml` | (workflow) |

