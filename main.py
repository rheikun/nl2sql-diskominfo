import streamlit as st
from modules.db_loader import load_database_metadata
from modules.db_utils import detect_relevant_databases, get_db_connection
from modules.search_generator import create_sql_agent_for_db
from modules.query_executor import run_with_error_tracking
from modules.answer_generator import create_answer_generator
from langchain.memory import ConversationBufferMemory

# Inisialisasi session
def initialize_session():
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    if "answer_generator" not in st.session_state:
        st.session_state.answer_generator = create_answer_generator(st.session_state.memory)
    if "database_metadata" not in st.session_state:
        st.session_state.database_metadata = load_database_metadata()
    if "chat_history_display" not in st.session_state:
        st.session_state.chat_history_display = []

# Proses query
def process_query(query):
    database_metadata = st.session_state.database_metadata
    memory = st.session_state.memory
    answer_generator = st.session_state.answer_generator

    # Ambil konteks dari history chat
    chat_history = memory.load_memory_variables({}).get("chat_history", [])
    context_words = set()
    for msg in chat_history[-3:]:
        context_words.update(msg.content.lower().split())
    keywords = set(query.lower().split()).union(context_words)
    full_query = " ".join(keywords)

    db_candidates = detect_relevant_databases(full_query, database_metadata)
    if not db_candidates:
        return "Tidak yakin database mana yang relevan."

    for db_name in db_candidates:
        try:
            db = get_db_connection(db_name)
            db_type = database_metadata[db_name]["db_type"]
            table_metadata = database_metadata[db_name]["tables"]

            agent_executor = create_sql_agent_for_db(db, db_type, memory)
            sql_query = run_with_error_tracking(agent_executor, query, table_metadata, db_type)

            if "SELECT" not in sql_query.upper():
                memory.save_context({"input": query}, {"output": sql_query})
                return sql_query

            result = db.run(sql_query)

            if not result:
                final_output = "Data tidak ditemukan."
            else:
                final_input = f"""
                Pertanyaan:
                {query}

                Hasil Query:
                {str(result)}
                """
                narasi = answer_generator.invoke({"input": final_input})
                final_output = narasi.get("text") or narasi.get("output")

            memory.save_context({"input": query}, {"output": final_output})
            return final_output

        except Exception as e:
            continue

    return "Gagal memproses query."

def display_chat():
    for msg in st.session_state.chat_history_display:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "agent":
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

def main():
    st.set_page_config(page_title="NL2SQL Multi-DB Chatbot", layout="centered")
    st.title("NL2SQL Multi-DB Chatbot")

    initialize_session()
    display_chat()

    user_query = st.chat_input("Tanyakan sesuatu...")
    if user_query:
        st.session_state.chat_history_display.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Memproses..."):
                response = process_query(user_query)
            st.markdown(response)

        st.session_state.chat_history_display.append({"role": "agent", "content": response})

# Jalankan aplikasi
if __name__ == "__main__":
    main()
