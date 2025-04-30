from langchain_community.utilities import SQLDatabase
from difflib import get_close_matches
from modules.db_loader import load_config

def detect_relevant_databases(query, database_metadata):
    from difflib import get_close_matches

    # Sinonim untuk membantu pemahaman semantik sederhana
    synonyms = {
        "mereka": ["pegawai", "penduduk", "orang"],
        "jumlah": ["total", "banyak", "count"],
        "nama": ["nama_pegawai", "nama_siswa", "nama_pelanggan", "nama_karyawan", "nama_layanan"]
    }

    query_words = set(query.lower().split())
    expanded_keywords = set(query_words)
    for word in query_words:
        expanded_keywords.update(synonyms.get(word, []))

    scores = {}
    for db_name, metadata in database_metadata.items():
        score = 0
        for table, columns in metadata["tables"].items():
            if any(word in table.lower() for word in expanded_keywords):
                score += 3

            if get_close_matches(table.lower(), expanded_keywords, cutoff=0.6):
                score += 2

            for column in columns:
                if any(word in column.lower() for word in expanded_keywords):
                    score += 1
                if get_close_matches(column.lower(), expanded_keywords, cutoff=0.6):
                    score += 0.5

        if any(word in db_name.lower() for word in expanded_keywords):
            score += 0.5

        scores[db_name] = score

    sorted_databases = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [db_name for db_name, score in sorted_databases if score > 0]

def get_db_connection(db_name, config_file="./config.json"):
    db_uris = load_config(config_file)
    if db_name not in db_uris:
        raise ValueError(f"Database '{db_name}' tidak ditemukan.")
    return SQLDatabase.from_uri(db_uris[db_name])

def adjust_sql_syntax(sql_query, db_type):
    if db_type == "oracle":
        sql_query = sql_query.rstrip(";")
        if "LIMIT" in sql_query.upper():
            limit = int(sql_query.split("LIMIT")[1].strip())
            base_query = sql_query.split("LIMIT")[0].strip()
            sql_query = f"SELECT * FROM ({base_query}) WHERE ROWNUM <= {limit}"
    elif db_type == "sqlserver":
        if "LIMIT" in sql_query.upper():
            limit = int(sql_query.split("LIMIT")[1].strip())
            base_query = sql_query.split("LIMIT")[0].strip()
            select_clause = base_query.split("SELECT")[1].strip()
            sql_query = f"SELECT TOP {limit} {select_clause}"
    return sql_query

def validate_sql_query(sql_query, db_type):
    if db_type in ["oracle", "sqlserver"]:
        if "LIMIT" in sql_query.upper():
            raise ValueError(f"Sintaks 'LIMIT' tidak didukung di {db_type}.")
    return sql_query
