import streamlit as st
import pypdf
from google import genai
import os

st.set_page_config(page_title="Jarvis Legal AI", page_icon="⚖️", layout="centered")

# --- ACEASTA ESTE PARTEA NOUĂ: MEMORIA ASCUNSĂ A LUI JARVIS ---
@st.cache_data # Asta face ca legea să fie citită o singură dată și ținută minte
def incarca_legislatia():
    # Verificăm dacă fișierul există pe GitHub
    if os.path.exists("legea_muncii.pdf"):
        cititor_lege = pypdf.PdfReader("legea_muncii.pdf")
        text_lege = ""
        for pagina in cititor_lege.pages:
            text_lege += pagina.extract_text()
        return text_lege
    else:
        return "Eroare: Nu am găsit fișierul legea_muncii.pdf în sistem."

# Încărcăm legea în fundal (utilizatorul nu vede asta)
text_legislatie_baza = incarca_legislatia()
# -------------------------------------------------------------

st.title("⚖️ Jarvis Legal AI")
st.subheader("Verifică-ți contractul de muncă")

st.sidebar.header("Setări Conexiune")
api_key = st.sidebar.text_input("Introdu cheia ta API Google Gemini:", type="password")

st.markdown("---")
st.markdown("### 1. Încarcă contractul tău (PDF)")
# Aici clientul încarcă DOAR contractul lui, nu și legea
fisier_incarcat = st.file_uploader("Trage contractul tău aici", type="pdf")

if fisier_incarcat is not None:
    cititor_contract = pypdf.PdfReader(fisier_incarcat)
    text_contract = ""
    for pagina in cititor_contract.pages:
        text_contract += pagina.extract_text()
        
    st.success("✅ Contractul tău a fost încărcat!")
        
    st.markdown("---")
    st.markdown("### 2. Consultanță Jarvis")
    
    intrebare = st.text_area("Ce vrei să afli?", placeholder="Ex: Este legală clauza de reziliere din acest contract?")
    
    if st.button("Verifică legalitatea", type="primary"):
        if not api_key:
            st.error("⚠️ Lipsă API Key în stânga!")
        else:
            with st.spinner("Jarvis compară contractul cu legea muncii..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    # PROMPT-UL MAGIC: Aici combinăm legea ascunsă cu contractul clientului
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
                    st.error(f"Eroare: {e}")
