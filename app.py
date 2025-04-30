from modules.db_loader import load_database_metadata
from modules.db_utils import detect_relevant_databases, get_db_connection
from modules.search_generator import create_sql_agent_for_db
from modules.query_executor import run_with_error_tracking
from modules.answer_generator import create_answer_generator
from langchain.memory import ConversationBufferMemory

def start_chat_session():
    database_metadata = load_database_metadata()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    answer_generator = create_answer_generator(memory)

    print("=== NL2SQL Multi-DB Chatbot Siap ===")
    while True:
        try:
            query = input("User > ")
            if query.lower() in ["exit", "quit"]:
                break

            chat_history = memory.load_memory_variables({}).get("chat_history", [])
            context_words = set()
            for msg in chat_history[-3:]:
                context_words.update(msg.content.lower().split())
            keywords = set(query.lower().split()).union(context_words)
            full_query = " ".join(keywords)

            db_candidates = detect_relevant_databases(full_query, database_metadata)
            if not db_candidates:
                print("Agent > Tidak yakin database mana yang relevan.")
                continue

            for db_name in db_candidates:
                try:
                    db = get_db_connection(db_name)
                    db_type = database_metadata[db_name]["db_type"]
                    table_metadata = database_metadata[db_name]["tables"]

                    agent_executor = create_sql_agent_for_db(db, db_type, memory)
                    sql_query = run_with_error_tracking(agent_executor, query, table_metadata, db_type)

                    if "SELECT" not in sql_query.upper():
                        print("Agent >", sql_query)
                        memory.save_context({"input": query}, {"output": sql_query})
                        break

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

                        narasi = answer_generator.invoke({
                            "input": final_input
                        })
                        final_output = narasi.get("text") or narasi.get("output")

                    print("Agent >", final_output)
                    memory.save_context({"input": query}, {"output": final_output})
                    break

                except Exception as e:
                    print(f"[ERROR] Gagal dengan DB {db_name}: {e}")
                    continue
        except KeyboardInterrupt:
            print("\n[INFO] Sesi dihentikan.")
            break

        
if __name__ == "__main__":
    start_chat_session()
    
    