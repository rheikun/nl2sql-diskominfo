from modules.db_utils import adjust_sql_syntax, validate_sql_query

def run_with_error_tracking(agent_executor, query, table_metadata, db_type, max_invalid=3, max_attempts=5):
    invalid_count = 0
    attempt_count = 0

    while invalid_count < max_invalid and attempt_count < max_attempts:
        try:
            print("\n[DEBUG] FINAL PROMPT VARIABLES:")
            print("Table Metadata:", table_metadata)
            print("User Question:", query)
            print("DB Type:", db_type)
            print("="*50)

            final_input = f"""Database Type: {db_type}
            Table Metadata: {str(table_metadata)}
            User Question: {query}"""

            response_dict = agent_executor.invoke({
                "input": final_input
            })

            print("[DEBUG] RAW OUTPUT DARI LLM:")
            print(response_dict["text"] if "text" in response_dict else response_dict.get("output", ""))
            print("="*50)

            raw_output = response_dict.get("text") or response_dict.get("output")
            if not raw_output:
                raise ValueError("LLM tidak menghasilkan output yang valid.")

            # Bersihkan markdown formatting
            raw_output = raw_output.strip()
            if raw_output.startswith("```sql"):
                raw_output = raw_output[6:]
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]
            raw_output = raw_output.strip()

            # Hapus quote jika ada
            if raw_output.startswith(("'", '"')) and raw_output.endswith(("'", '"')):
                raw_output = raw_output[1:-1]


            validated_query = validate_sql_query(raw_output, db_type=db_type)
            adjusted_sql_query = adjust_sql_syntax(validated_query, db_type=db_type)
            return adjusted_sql_query

        except Exception as e:
            print(f"[ERROR] Attempt {attempt_count+1}: {e}")
            attempt_count += 1
            invalid_count += 1
            if attempt_count >= max_attempts:
                return "Maaf, terjadi kesalahan dalam memproses permintaan Anda."
    return "Tidak dapat memproses permintaan."
