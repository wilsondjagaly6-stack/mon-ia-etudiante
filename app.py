import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import time

# --- CONFIGURATION STYLE ---
st.set_page_config(page_title="Mon Assistant Études", layout="wide")

# Masquer le menu Streamlit pour faire plus "Pro"
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stChatFloatingInputContainer {padding-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
if "prenom" not in st.session_state:
    st.session_state.prenom = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_text" not in st.session_state:
    st.session_state.full_text = ""

# --- CONNEXION API ---
# La clé sera configurée dans l'interface de Streamlit Cloud (Secrets)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
else:
    st.error("Configuration API manquante. Contacte l'administrateur.")

# --- ÉCRAN D'ACCUEIL ---
if not st.session_state.prenom:
    st.title("🚀 Bienvenue dans ton Workspace")
    prenom_input = st.text_input("Salut ! C'est quoi ton prénom ?", placeholder="Ex: Jean...")
    if st.button("Entrer dans l'espace de travail"):
        if prenom_input:
            st.session_state.prenom = prenom_input
            st.rerun()
        else:
            st.warning("Donne-moi ton petit nom d'abord !")
else:
    # --- INTERFACE PRINCIPALE ---
    with st.sidebar:
        st.title(f"🎓 Espace de {st.session_state.prenom}")
        st.write("---")
        uploaded_files = st.file_uploader("Charge tes cours (PDF)", accept_multiple_files=True)
        
        if st.button("Effacer la discussion"):
            st.session_state.messages = []
            st.rerun()

    # Traitement des fichiers
    if uploaded_files and not st.session_state.full_text:
        with st.status("Analyse des documents en cours...", expanded=True) as status:
            context = ""
            for uploaded_file in uploaded_files:
                reader = PdfReader(uploaded_file)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        context += f"\n[SOURCE: {uploaded_file.name}, PAGE: {i+1}]\n{text}\n"
            st.session_state.full_text = context
            status.update(label="Analyse terminée ! Je connais tes cours par cœur.", state="complete")

    # Affichage du Chat
    st.title(f"On bosse sur quoi, {st.session_state.prenom} ?")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pose ta question ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.full_text:
                full_prompt = f"""
                Utilisateur: {st.session_state.prenom}
                Contexte des cours: {st.session_state.full_text[:30000]} 
                Instruction: Réponds à {st.session_state.prenom}. Sois précis. 
                Cite obligatoirement les sources sous la forme [Nom du fichier, Page X].
                Question: {prompt}
                """
                response = model.generate_content(full_prompt)
                full_response = response.text
            else:
                full_response = f"Désolé {st.session_state.prenom}, tu n'as pas encore chargé de documents dans la barre latérale !"
            
            st.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})
