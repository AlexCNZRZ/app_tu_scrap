import streamlit as st
import requests
import json

st.set_page_config(page_title="Zscaler Checker (Cloud)", layout="wide")

# ==============================
# FUNCTION : CALL ZSCALER BACKEND
# ==============================
def get_zscaler_data(url):

    try:
        endpoint = "https://sitereview.zscaler.com/api/v1/urlinfo"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }

        payload = {
            "url": url
        }

        response = requests.post(endpoint, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# ==============================
# UI
# ==============================
st.title("🔍 Zscaler URL Checker (Streamlit Cloud Compatible)")

url = st.text_input("Saisir une URL")

if st.button("Analyser"):

    if not url:
        st.warning("Veuillez entrer une URL")
    else:
        with st.spinner("Analyse en cours..."):

            data = get_zscaler_data(url)

        if "error" in data:
            st.error(data["error"])
        else:
            st.success("Résultat récupéré")

            # 🔍 JSON brut
            st.subheader("📦 Réponse complète")
            st.json(data)

            # 🎯 Extraction utile (si dispo)
            try:
                category = data.get("category", "Inconnue")
                reputation = data.get("reputation", "N/A")

                st.subheader("🎯 Résumé")
                st.write(f"Catégorie : **{category}**")
                st.write(f"Réputation : **{reputation}**")

            except:
                st.warning("Impossible d'extraire les champs principaux")
