import streamlit as st
import pypdf
from google import genai
import os

st.set_page_config(page_title="Jarvis Legal AI", page_icon="⚖️", layout="centered")

# ==========================================
# SISTEMUL DE AUTENTIFICARE (LOGIN)
# ==========================================
def verifica_parola():
    """Returnează True dacă utilizatorul s-a logat corect."""
    
    # Funcția care se rulează când apeși pe butonul de Login
    def validare_date():
        if (st.session_state["username"] == st.secrets["APP_USER"] and 
            st.session_state["password"] == st.secrets["APP_PASS"]):
            st.session_state["logat"] = True
            # Ștergem datele din memorie pentru securitate
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["logat"] = False

    # Dacă nu există starea 'logat', arătăm formularul
    if "logat" not in st.session_state:
        st.title("🔒 Autentificare Jarvis Legal")
        st.text_input("Utilizator", key="username")
        st.text_input("Parolă", type="password", key="password")
        st.button("Intră în cont", on_click=validare_date)
        return False
    # Dacă a greșit parola, arătăm eroare
    elif not st.session_state["logat"]:
        st.title("🔒 Autentificare Jarvis Legal")
        st.text_input("Utilizator", key="username")
        st.text_input("Parolă", type="password", key="password")
        st.button("Intră în cont", on_click=validare_date)
        st.error("😕 Utilizator sau parolă incorectă.")
        return False
    # Dacă totul e corect, mergem mai departe
    else:
        return True

# BARIERA: Dacă funcția de mai sus returnează False, oprim tot codul aici!
if not verifica_parola():
    st.stop()

# ==========================================
# APLICAȚIA PRINCIPALĂ (Rulează doar dacă ești logat)
# ==========================================

# Luăm cheia API direct din "seiful" Streamlit, fără ca utilizatorul s-o vadă
api_key_secret = st.secrets["GEMINI_API_KEY"]

# --- MEMORIA ASCUNSĂ A LUI JARVIS ---
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
        return "Eroare: Nu am găsit fișierul legea_muncii.pdf în sistem."

text_legislatie_baza = incarca_legislatia()
# -------------------------------------------------------------

# Nu mai avem nevoie de bara laterală pentru API Key!
st.title("⚖️ Jarvis Legal AI")
st.subheader("Bine ai venit în contul tău securizat!")

# Buton de Logout opțional
if st.button("Ieși din cont (Logout)"):
    st.session_state.clear()
    st.rerun()

st.markdown("---")
st.markdown("### 1. Încarcă contractul tău (PDF)")
fisier_incarcat = st.file_uploader("Trage contractul tău aici", type="pdf")

if fisier_incarcat is not None:
    cititor_contract = pypdf.PdfReader(fisier_incarcat)
    text_contract = ""
    for pagina in cititor_contract.pages:
        extras = pagina.extract_text()
        if extras:
            text_contract += extras
            
    text_contract = text_contract.encode('utf-8', 'ignore').decode('utf-8')
        
    st.success("✅ Contractul tău a fost încărcat!")
        
    st.markdown("---")
    st.markdown("### 2. Consultanță Jarvis")
    
    intrebare = st.text_area("Ce vrei să afli?", placeholder="Ex: Este legală clauza de reziliere din acest contract?")
    
    if st.button("Verifică legalitatea", type="primary"):
        with st.spinner("Jarvis compară contractul cu legea muncii..."):
            try:
                # Folosim cheia ascunsă preluată mai sus
                client = genai.Client(api_key=api_key_secret)
                
                prompt_final = f"""
                Ești un avocat expert în dreptul muncii din România. 
                Mai jos ai LEGISLAȚIA (Codul Muncii) și CONTRACTUL clientului.
                Răspunde la întrebarea clientului verificând dacă contractul respectă legislația furnizată.
                
                --- LEGISLAȚIE (Codul Muncii) ---
                {text_legislatie_baza}
                
                --- CONTRACTUL CLIENTULUI ---
                {text_contract}
                
                --- ÎNTREBAREA CLIENTULUI ---
                {intrebare}
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_final,
                )
                
                st.markdown("### 💡 Raport Juridic:")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Eroare AI: {e}")
