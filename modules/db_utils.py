import re
import logging
from langchain_community.utilities import SQLDatabase
from difflib import get_close_matches
from modules.db_loader import load_config

logging.basicConfig(level=logging.INFO)

STOPWORDS = {
    "tampilkan", "data", "yang", "ada", "itu", "semua", "list", "daftar", 
    "kominfo", "show", "get", "lihat", "cari", "ambil"
}

def detect_relevant_databases(query, database_metadata):
    query_words = set(re.findall(r"\w+", query.lower())) - STOPWORDS
    scores = {}

    for db_name, metadata in database_metadata.items():
        score = 0
        for table, columns in metadata["tables"].items():
            table_lower = table.lower()
            table_words = set(table_lower.split("_"))

            for word in query_words:
                if word in table_lower:
                    score += 5  
                elif word in table_words:
                    score += 3
                elif get_close_matches(word, table_words, cutoff=0.6):
                    score += 2
                
            for column in columns:
                column_lower = column.lower()
                for word in query_words:
                    if word in column_lower:
                        score += 1
                    elif get_close_matches(word, [column_lower], cutoff=0.6):
                        score += 0.5

        for word in query_words:
            if word in db_name.lower():
                score += 0.5

        scores[db_name] = score

    sorted_databases = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    logging.info(f"[DB Detection] Keywords: {query_words}")
    logging.info(f"[DB Detection] Scores: {scores}")
    logging.info(f"[DB Detection] Top Match: {sorted_databases[:3]}")

    return [db_name for db_name, score in sorted_databases if score > 0]

def get_db_connection(db_name, config_file="./config.json"):
    db_uris = load_config(config_file)
    if db_name not in db_uris:
        raise ValueError(f"Database '{db_name}' tidak ditemukan.")
    return SQLDatabase.from_uri(db_uris[db_name])

def adjust_sql_syntax(sql_query, db_type):
    sql_query = sql_query.rstrip(";")

    if any(x in sql_query.upper() for x in ["FETCH FIRST", "TOP"]):
        return sql_query

    if "LIMIT" in sql_query.upper():
        match = re.search(r"LIMIT\s+(\d+)", sql_query, re.IGNORECASE)
        if match:
            limit = int(match.group(1))
            sql_query = re.sub(r"(?i)\s+LIMIT\s+\d+", "", sql_query)

            if db_type == "oracle":
                sql_query += f" FETCH FIRST {limit} ROWS ONLY"
            elif db_type == "sqlserver":
                sql_query = re.sub(r"(?i)^SELECT\s", f"SELECT TOP {limit} ", sql_query, count=1)
    return sql_query

def validate_sql_query(sql_query, db_type):
    if db_type in ["oracle", "sqlserver"] and "LIMIT" in sql_query.upper():
        raise ValueError(f"Sintaks 'LIMIT' tidak didukung di {db_type}.")
    return sql_query

def is_ambiguous(query: str) -> bool:
    ambiguous_patterns = [
        "yang lainnya", "gimana", "bagaimana", "lanjut", "terus", 
        "itu aja", "dan?", "iya", "selain itu", "ada lagi", 
        "yang tadi", "apa lagi"
    ]
    return any(phrase in query.lower() for phrase in ambiguous_patterns)