import streamlit as st
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================
# CONFIG
# ==============================
CSV_URL = "https://help.zscaler.com/downloads/zia/documentation-knowledgebase/policies/url-filtering/about-url-categories/ZIA-URLCategories-02-12-2025.csv"

st.set_page_config(page_title="Zscaler Checker FINAL", layout="wide")

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
# DRIVER (FIREFOX CLOUD SAFE)
# ==============================
def create_driver():
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options
    )

    return driver

# ==============================
# SCRAPING ZSCALER
# ==============================
def scrape_category(url):

    driver = create_driver()

    try:
        driver.get("https://sitereview.zscaler.com/")
        wait = WebDriverWait(driver, 20)

        # attendre chargement
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # trouver input
        input_box = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input"))
        )

        # injecter URL via JS (fiable)
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        """, input_box, url)

        time.sleep(1)

        # trouver bouton
        button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button"))
        )

        # clic JS
        driver.execute_script("arguments[0].click();", button)

        # attendre résultat
        time.sleep(5)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        return body_text

    except Exception as e:
        return f"Erreur: {e}"

    finally:
        driver.quit()

# ==============================
# UI
# ==============================
st.title("🔐 Zscaler URL Policy Checker (FINAL Cloud Version)")

tab1, tab2 = st.tabs(["📂 Catégories", "🔍 Tester URL"])

# ==============================
# TAB 1
# ==============================
with tab1:
    st.header("Gestion des catégories")

    cols = st.columns(3)

    for i, cat in enumerate(categories):
        with cols[i % 3]:
            val = st.toggle(cat, value=st.session_state.rules.get(cat, True))
            st.session_state.rules[cat] = val

# ==============================
# TAB 2
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

            st.subheader("Résultat brut")
            st.text_area("Réponse", result, height=300)

            # tentative extraction catégorie simple
            detected_category = None

            for cat in categories:
                if cat.lower() in result.lower():
                    detected_category = cat
                    break

            if detected_category:
                st.subheader("Catégorie détectée")
                st.write(detected_category)

                if st.session_state.rules.get(detected_category, True):
                    st.success("✅ URL AUTORISÉE")
                else:
                    st.error("❌ URL REFUSÉE")
            else:
                st.warning("Catégorie non détectée automatiquement")

            except:
                st.warning("Impossible d'extraire les champs principaux")
