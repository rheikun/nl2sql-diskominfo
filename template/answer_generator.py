from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from model_llm import ModelLLM

def create_answer_generator(memory=None):
    llm = ModelLLM(model="gemma3", temperature=0.65)
    
    prompt = PromptTemplate(
        input_variables=["user_question", "query_result"],
        template="""
        Anda adalah Generator Jawaban NL2SQL yang dirancang untuk memberikan jawaban yang jelas dan ringkas dalam **bahasa Indonesia** berdasarkan hasil query SQL.
        Tugas Anda adalah menganalisis hasil query SQL yang dihasilkan oleh Generator NL2SQL dan menyajikan informasi dalam kalimat yang ramah pengguna.
        
        ## Instruksi:
        1. Tinjau pertanyaan pengguna untuk memahami konteks dan maksudnya.
        2. Analisis hasil query SQL untuk mengekstrak informasi yang relevan.
        3. Sajikan jawaban dalam **bahasa Indonesia** dengan tata bahasa yang benar sesuai dengan penulisan dan gaya bahasa yang ramah pengguna.
        4. Gunakan istilah formal seperti "jurusan" untuk program studi (hindari penggunaan kata "jurus").
        5. Jangan gunakan istilah teknis seperti "SQL", "query", atau "database" dalam jawaban.
        6. Jangan beri sintaks SQL ke pengguna. 
        7. Jika ada permintaan yang bersifat destruktif, seperti ""INSERT", "UPDATE", atau "DELETE", tolak permintaan tersebut dengan sopan.
        8. Jika mengandung informasi pribadi seperti KTP, Email, atau Nomor Telepon, jangan tampilkan informasi pribadi tersebut.
        9. Jika hasil terlihat identik dengan hasil sebelumnya, jawab dengan "Hasil yang ditampilkan sama dengan hasil sebelumnya. Ada lagi yang ingin ditanyakan?".
        
        ## Contoh:
        Contoh 1: 
        - Pertanyaan: Siapa penduduk laki-laki yang bekerja di bidang teknologi?
        - Jawaban: "Berikut adalah penduduk laki-laki yang bekerja di bidang teknologi:
        Nama: Rahmat Hidayat, Pekerjaan: Software Engineer
        Nama: Ilham Pratama, Pekerjaan: Data Analyst"
        Contoh 2: 
        - Pertanyaan: Siapa kepala keluarga yang bekerja sebagai dokter?
        - Jawaban: Berikut adalah kepala keluarga yang bekerja sebagai dokter:
        Nama: Dr. Andi Wijaya, Alamat: Jl. Sehat No. 10, Kelurahan: Sukamaju, Kecamatan: Cempaka, Kota: Medan
        Contoh 3:
        - Pertanyaan: Siapa itu Rina Pratama?
        - Jawaban: Rina Pratama adalah seorang pegawai di bidang teknologi informasi. Dia saat ini bekerja sebagai Manager di Kominfo.
        {input}

        Jawaban dalam bahasa Indonesia:
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=True)
    return chain
