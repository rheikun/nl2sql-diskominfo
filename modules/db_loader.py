import json

# ====================== MEMUAT METADATA DAN URI DB ======================
def load_database_metadata(json_file="./db_metadata.json"):
    try:
        with open(json_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File metadata '{json_file}' tidak ditemukan.")
    except json.JSONDecodeError:
        raise ValueError("Format file metadata tidak valid.")

def load_config(config_file="./config.json"):
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File konfigurasi '{config_file}' tidak ditemukan.")
    except json.JSONDecodeError:
        raise ValueError("Format file konfigurasi tidak valid.")
