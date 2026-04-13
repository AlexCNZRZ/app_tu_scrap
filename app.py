import streamlit as st
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================
# CONFIG
# ==============================
CSV_URL = "https://help.zscaler.com/downloads/zia/documentation-knowledgebase/policies/url-filtering/about-url-categories/ZIA-URLCategories-02-12-2025.csv"

st.set_page_config(page_title="Zscaler Checker", layout="wide")

# ==============================
# LOAD CATEGORIES
# ==============================
@st.cache_data
def load_categories():
    df = pd.read_csv(CSV_URL)
    if "Category" in df.columns:
        return df["Category"].dropna().unique().tolist()
    return df.iloc[:, 0].dropna().unique().tolist()

categories = load_categories()

# ==============================
# SESSION STATE
# ==============================
if "rules" not in st.session_state:
    st.session_state.rules = {cat: True for cat in categories}

# ==============================
# SELENIUM DRIVER
# ==============================
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # IMPORTANT pour Docker / VPS
    options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=options)
    return driver

# ==============================
# SCRAPING + EXTRACTION
# ==============================
def scrape_category(url):

    driver = create_driver()

    try:
        driver.get("https://sitereview.zscaler.com/")
        wait = WebDriverWait(driver, 20)

        # attendre chargement complet
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # récupérer les inputs visibles
        inputs = driver.find_elements(By.XPATH, "//input")

        input_box = None
        for inp in inputs:
            if inp.is_displayed() and inp.is_enabled():
                input_box = inp
                break

        if not input_box:
            raise Exception("Champ de saisie introuvable")

        # interaction réelle
        input_box.clear()
        input_box.send_keys(url)
        time.sleep(1)

        # envoi réel
        input_box.send_keys(Keys.ENTER)

        # attendre résultat
        time.sleep(5)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        # ==============================
        # EXTRACTION CATEGORIE
        # ==============================
        category = None
        lines = body_text.split("\n")

        for line in lines:
            if "Category" in line or "URL Category" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    category = parts[1].strip()
                    break

        # fallback simple
        if not category:
            for line in lines:
                if 3 < len(line) < 50:
                    category = line.strip()
                    break

        return {
            "category": category,
            "raw_text": body_text
        }

    except Exception as e:
        return {
            "error": str(e)
        }

    finally:
        driver.quit()

# ==============================
# UI
# ==============================
st.title("🔐 Zscaler URL Policy Checker")

tab1, tab2 = st.tabs(["📂 Catégories", "🔍 Tester une URL"])

# ==============================
# TAB 1 : REGLES
# ==============================
with tab1:
    st.header("Gestion des catégories")

    cols = st.columns(3)

    for i, cat in enumerate(categories):
        with cols[i % 3]:
            val = st.toggle(cat, value=st.session_state.rules.get(cat, True))
            st.session_state.rules[cat] = val

# ==============================
# TAB 2 : TEST URL
# ==============================
with tab2:
    st.header("Tester une URL")

    url = st.text_input("Entrer une URL")

    if st.button("Analyser"):

        if not url:
            st.warning("Veuillez entrer une URL")
        else:
            with st.spinner("Analyse en cours..."):

                result = scrape_category(url)

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("🎯 Catégorie détectée")

                if result["category"]:
                    st.success(result["category"])

                    # vérification règle
                    if result["category"] in st.session_state.rules:
                        if st.session_state.rules[result["category"]]:
                            st.success("✅ URL AUTORISÉE")
                        else:
                            st.error("❌ URL REFUSÉE")
                    else:
                        st.warning("Catégorie non trouvée dans la liste")

                else:
                    st.warning("Catégorie non détectée")

                # debug
                with st.expander("🔍 Voir le texte complet"):
                    st.text(result["raw_text"])
