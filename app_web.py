import streamlit as st
import pypdf
from google import genai

# 1. Setările paginii (Titlu și aspect)
st.set_page_config(page_title="Jarvis Legal AI", page_icon="⚖️", layout="centered")

st.title("⚖️ Jarvis Legal AI")
st.subheader("Asistentul tău pentru analiza contractelor")

# 2. Bara laterală (Sidebar) pentru Securitate - Aici utilizatorul pune cheia API
st.sidebar.header("Setări Conexiune")
api_key = st.sidebar.text_input("AIzaSyCC3xtCavzu1GJAa9TUU4IdOndCbwDGiuM", type="password")
st.sidebar.markdown("*Nu ai o cheie? [Obține una gratuită aici](https://aistudio.google.com/app/apikey)*")

# 3. Modulul de încărcare a contractului
st.markdown("---")
st.markdown("### 1. Încarcă documentul")
fisier_incarcat = st.file_uploader("Trage un contract (format PDF) aici", type="pdf")

# 4. Logica principală: Dacă avem fișier, mergem mai departe
if fisier_incarcat is not None:
    # Citim PDF-ul
    cititor = pypdf.PdfReader(fisier_incarcat)
    text_contract = ""
    for pagina in cititor.pages:
        text_contract += pagina.extract_text()
        
    st.success("✅ Contract citit și memorat cu succes!")
    
    # Previzualizare opțională
    with st.expander("Vezi textul extras din PDF"):
        st.write(text_contract[:1000] + "\n\n... [Textul continuă] ...")
        
    st.markdown("---")
    st.markdown("### 2. Consultanță Jarvis")
    
    # Căsuța pentru întrebarea utilizatorului
    intrebare = st.text_area("Ce vrei să verifici în acest contract?", 
                             placeholder="Exemplu: Care sunt clauzele de reziliere? Există penalități?")
    
    # Butonul de declanșare a AI-ului
    if st.button("Analizează Contractul", type="primary"):
        if not api_key:
            st.error("⚠️ Te rog să introduci cheia API Gemini în meniul din stânga!")
        elif not intrebare:
            st.warning("⚠️ Scrie o întrebare înainte de a apăsa butonul.")
        else:
            with st.spinner("Jarvis analizează clauzele... Te rog așteaptă."):
                try:
                    # Conectarea la "Creierul" Gemini
                    client = genai.Client(api_key=api_key)
                    
                    # Îi dăm AI-ului instrucțiunile clare și textul contractului
                    prompt_final = f"""
                    Ești un avocat de elită și un asistent juridic expert. 
                    Analizează următorul contract și răspunde la întrebarea utilizatorului strict pe baza textului furnizat.
                    Dacă informația cerută nu se află în contract, spune asta clar, nu inventa.
                    
                    CONTRACT:
                    {text_contract}
                    
                    ÎNTREBARE:
                    {intrebare}
                    """
                    
                    # Generăm răspunsul
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_final,
                    )
                    
                    # Afișăm rezultatul
                    st.markdown("### 💡 Răspunsul lui Jarvis:")
                    st.info(response.text)
                    
                except Exception as e:
                    st.error(f"A apărut o eroare la conexiunea cu AI. Verifică API Key-ul. Detalii eroare: {e}")
else:
    st.info("Aștept să încarci un contract PDF pentru a începe.")


