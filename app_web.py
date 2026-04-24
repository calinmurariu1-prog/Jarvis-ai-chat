import streamlit as st
import pypdf
from google import genai
import os

st.set_page_config(page_title="Jarvis Legal AI", page_icon="⚖️", layout="centered")

# ==========================================
# 1. AUTENTIFICAREA (Păstrată pentru acces)
# ==========================================
def verifica_parola():
    def validare_date():
        if (st.session_state["username"] == st.secrets["APP_USER"] and 
            st.session_state["password"] == st.secrets["APP_PASS"]):
            st.session_state["logat"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["logat"] = False

    if "logat" not in st.session_state:
        st.title("🔒 Jarvis Legal - Acces Cont")
        st.info("Aceasta este o platformă premium. Te rugăm să te autentifici.")
        st.text_input("Utilizator", key="username")
        st.text_input("Parolă", type="password", key="password")
        st.button("Intră în cont", on_click=validare_date)
        return False
    elif not st.session_state["logat"]:
        st.title("🔒 Jarvis Legal - Acces Cont")
        st.text_input("Utilizator", key="username")
        st.text_input("Parolă", type="password", key="password")
        st.button("Intră în cont", on_click=validare_date)
        st.error("😕 Utilizator sau parolă incorectă.")
        return False
    else:
        return True

if not verifica_parola():
    st.stop()

# ==========================================
# 2. APLICAȚIA PRINCIPALĂ (Interfață tip Chat + Disclaimer)
# ==========================================
api_key_secret = st.secrets["GEMINI_API_KEY"]

@st.cache_data 
def incarca_legislatia():
    if os.path.exists("legea_muncii.pdf"):
        cititor_lege = pypdf.PdfReader("legea_muncii.pdf")
        text_lege = ""
        for pagina in cititor_lege.pages:
            extras = pagina.extract_text()
            if extras:
                text_lege += extras
        return text_lege.encode('utf-8', 'ignore').decode('utf-8')
    else:
        return "Eroare: Baza de date legislativă lipsește."

text_legislatie_baza = incarca_legislatia()

# --- DESIGN PAGINĂ ---
col1, col2 = st.columns([4, 1])
with col1:
    st.title("⚖️ Jarvis Legal AI")
with col2:
    if st.button("Ieși (Logout)"):
        st.session_state.clear()
        st.rerun()

st.markdown("---")

# --- MEMORIA CHAT-ULUI ---
if "mesaje" not in st.session_state:
    st.session_state["mesaje"] = [{"rol": "asistent", "continut": "Salut! Sunt Jarvis. Încarcă un contract și pune-mi o întrebare despre el."}]
if "text_contract" not in st.session_state:
    st.session_state["text_contract"] = ""

# --- ZONA DE UPLOAD ---
fisier_incarcat = st.file_uploader("📂 Încarcă documentul tău (PDF)", type="pdf")

if fisier_incarcat is not None:
    # Citim doar dacă este un fișier nou
    if fisier_incarcat.name not in st.session_state.get("nume_fisier", ""):
        cititor_contract = pypdf.PdfReader(fisier_incarcat)
        text_contract = ""
        for pagina in cititor_contract.pages:
            extras = pagina.extract_text()
            if extras:
                text_contract += extras
        st.session_state["text_contract"] = text_contract.encode('utf-8', 'ignore').decode('utf-8')
        st.session_state["nume_fisier"] = fisier_incarcat.name
        st.success(f"✅ Contractul '{fisier_incarcat.name}' a fost încărcat și analizat!")

st.markdown("---")

# --- PROTECȚIA JURIDICĂ (DISCLAIMER OBLIGATORIU) ---
acord_legal = st.checkbox("Sunt de acord că Jarvis oferă informații generale, nu consultanță juridică oficială.")

# --- AFIȘAREA CHAT-ULUI ---
for mesaj in st.session_state["mesaje"]:
    with st.chat_message("assistant" if mesaj["rol"] == "asistent" else "user"):
        st.markdown(mesaj["continut"])

# --- ZONA DE ÎNTREBĂRI (Funcționează doar dacă s-a bifat acordul) ---
intrebare = st.chat_input("Scrie întrebarea ta aici...")

if intrebare:
    if not acord_legal:
        st.warning("⚠️ Trebuie să bifezi căsuța de acord legal pentru a putea comunica cu Jarvis.")
    elif not st.session_state["text_contract"]:
        st.warning("⚠️ Te rog să încarci un contract PDF mai întâi.")
    else:
        # Afișăm întrebarea utilizatorului
        st.session_state["mesaje"].append({"rol": "utilizator", "continut": intrebare})
        with st.chat_message("user"):
            st.markdown(intrebare)
            
        # Răspunsul AI-ului
        with st.chat_message("assistant"):
            with st.spinner("Jarvis caută în legislație..."):
                try:
                    client = genai.Client(api_key=api_key_secret)
                    
                    prompt_final = f"""
                    Ești un avocat expert în dreptul muncii din România. 
                    
                    ISTORICUL CONVERSAȚIEI:
                    {st.session_state["mesaje"][-3:]} # Îi dăm AI-ului ultimele mesaje ca să țină minte contextul
                    
                    Răspunde la ultima întrebare a clientului verificând dacă contractul respectă legislația furnizată.
                    Regulă de aur: Menționează mereu Articolul din lege pe care te bazezi.
                    
                    --- LEGISLAȚIE (Codul Muncii) ---
                    {text_legislatie_baza}
                    
                    --- CONTRACTUL CLIENTULUI ---
                    {st.session_state["text_contract"]}
                    
                    --- ULTIMA ÎNTREBARE A CLIENTULUI ---
                    {intrebare}
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_final,
                    )
                    
                    raspuns_ai = response.text
                    st.markdown(raspuns_ai)
                    st.session_state["mesaje"].append({"rol": "asistent", "continut": raspuns_ai})
                    
                except Exception as e:
                    st.error(f"Eroare AI: {e}")

