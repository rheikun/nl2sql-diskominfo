import random
import re
import difflib
from modules.search_generator import create_sql_agent_for_db
from modules.answer_generator import generate_answer
from modules.db_loader import load_database
from modules.db_utils import get_db_metadata
from modules.query_executor import execute_query
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def detect_and_correct_typo(user_input: str, vocab: list) -> str:
    words = user_input.split()
    corrected_words = []
    for word in words:
        if word.lower() not in vocab:
            suggestions = difflib.get_close_matches(word.lower(), vocab, n=1, cutoff=0.8)
            corrected_words.append(suggestions[0] if suggestions else word)
        else:
            corrected_words.append(word)
    return " ".join(corrected_words)

def is_destructive_sql(query: str) -> bool:
    destructive_keywords = ["drop", "delete", "truncate", "alter", "update", "insert"]
    return any(re.search(rf"\\b{kw}\\b", query, re.IGNORECASE) for kw in destructive_keywords)

def process_user_input(user_input, db_name):
    metadata = get_db_metadata(db_name)
    vocab = metadata.get("vocab", [])
    db_type = metadata.get("db_type", "MySQL")
    db = load_database(db_name)

    corrected_input = detect_and_correct_typo(user_input, vocab)

    try:
        agent = create_sql_agent_for_db(db, db_type, memory)
        sql_query = agent.run(corrected_input)
    except Exception as e:
        return f"[{db_name}] ❌ Gagal membuat query SQL: {e}"

    if is_destructive_sql(sql_query):
        return f"[{db_name}] ⚠️ Query mengandung perintah destruktif dan tidak dieksekusi."

    try:
        results = execute_query(sql_query, db_name)
    except Exception as e:
        return f"[{db_name}] ❌ Eksekusi query gagal: {e}"

    try:
        return f"[{db_name}] " + generate_answer(results, corrected_input)
    except:
        fallback_responses = [
            f"[{db_name}] Maaf, saya belum bisa menjawab pertanyaan tersebut.",
            f"[{db_name}] Pertanyaan ini terlalu kompleks untuk saya jawab.",
            f"[{db_name}] Saya tidak menemukan jawaban yang sesuai."
        ]
        return random.choice(fallback_responses)
