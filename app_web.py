
import streamlit as st
from google import genai
import PyPDF2
import subprocess

# 1. Configurare Pagină - Numele JARVIS apare în tab-ul browserului
st.set_page_config(page_title="JARVIS AI", page_icon="🎙️", layout="wide")
st.title("🎙️ JARVIS - Asistent Cybernetic")

# Cheia ta API
CHEIE_API = st.secrets["GOOGLE_API_KEY"]

# Inițializăm memoria dacă nu există
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- MENIUL LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("📁 1. Analiză Fișiere")
    fisier_incarcat = st.file_uploader("Încarcă TXT, PDF, PY sau SH", type=["txt", "pdf", "py", "sh"])
    
    st.divider()
    
    st.header("⚡ 2. Terminal Rapid")
    st.write("Rulează o comandă Linux (ex: `ping -c 2 google.com`)")
    comanda = st.text_input("Comandă:")
    if st.button("Rulează Comanda"):
        if comanda:
            try:
                rezultat = subprocess.run(comanda, shell=True, capture_output=True, text=True)
                output = rezultat.stdout if rezultat.stdout else rezultat.stderr
                
                # Mesajul pe care JARVIS îl va primi pentru a-l explica
                mesaj_terminal = f"Am rulat comanda: `{comanda}`.\n\nRezultat:\n```text\n{output}\n```\nJARVIS, explică-mi te rog acest rezultat."
                st.session_state.messages.append({"role": "user", "content": mesaj_terminal})
                st.rerun() 
            except Exception as e:
                st.error(f"Eroare terminal: {e}")

    st.divider()
    
    st.header("💾 3. Salvare Raport")
    if st.session_state.messages:
        chat_export = ""
        for m in st.session_state.messages:
            rol = "JARVIS" if m['role'] == "assistant" else "TU"
            chat_export += f"--- {rol} ---\n{m['content']}\n\n"
        
        st.download_button("📥 Descarcă Log Conversație", data=chat_export, file_name="Raport_JARVIS.txt")

# --- ZONA DE CHAT PRINCIPALĂ ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Când scrii un mesaj manual
prompt = st.chat_input("Cu ce te pot ajuta, domnule?")

ultimul_mesaj_e_user = len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user"

if prompt or (ultimul_mesaj_e_user and prompt is None):
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

    try:
        client = genai.Client(api_key=CHEIE_API)
        
        # PROCESAREA FIȘIERELOR
        text_fisier = ""
        if fisier_incarcat is not None and prompt is not None:
            if fisier_incarcat.name.endswith(".pdf"):
                cititor_pdf = PyPDF2.PdfReader(fisier_incarcat)
                text_fisier = "".join([pagina.extract_text() for pagina in cititor_pdf.pages])
            else:
                text_fisier = fisier_incarcat.getvalue().decode("utf-8", errors="ignore")
            
            text_fisier = f"\n\n[SURSĂ DATE]:\n{text_fisier}"

        # Pregătim istoricul pentru AI
        istoric_complet = []
        
        # ==============================================================
        # PUNCTUL 1 APLICAT: Luăm doar ultimele 6 mesaje din memorie
        # ==============================================================
        mesaje_recente = st.session_state.messages[-6:] 
        
        for i, msg in enumerate(mesaje_recente):
            rol_gemini = "user" if msg["role"] == "user" else "model"
            text_mesaj = msg["content"]
            
            # Lipim textul fișierului doar de ultimul mesaj din listă
            if i == len(mesaje_recente) - 1 and text_fisier != "":
                text_mesaj += text_fisier

            istoric_complet.append({"role": rol_gemini, "parts": [{"text": text_mesaj}]})
            
        # INSTRUCȚIUNILE DE SISTEM
        system_prompt = (
            "Numele tău este JARVIS. Ești un asistent cybernetic sofisticat, similar cu inteligența artificială a lui Tony Stark, "
            "dar specializat pentru Kali Linux. Răspunzi mereu în limba română, ești extrem de politicos, inteligent și concis. "
            "Dacă ți se oferă date din terminal sau fișiere, analizează-le cu rigoare tehnică."
        )

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=istoric_complet,
            config={'system_instruction': system_prompt}
        )
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
    except Exception as e:
        st.error(f"Eroare sistem: {e}")

