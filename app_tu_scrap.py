import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from fake_useragent import UserAgent
import time
import random

st.set_page_config(page_title="Zscaler Scraper PRO", layout="wide")

# ==============================
# DRIVER STEALTH
# ==============================


def create_driver():
    ua = UserAgent()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"user-agent={ua.random}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # 🔥 Anti-détection JS
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """)

    return driver

# ==============================
# SCRAPING EXPERT
# ==============================


def scrape_zscaler(url_to_test, retries=2):

    for attempt in range(retries):

        driver = create_driver()

        try:
            driver.get("https://sitereview.zscaler.com/")
            wait = WebDriverWait(driver, 20)

            # ⏳ Attendre que la page soit stable
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

            time.sleep(random.uniform(2, 4))

            # 🔍 Trouver TOUS les inputs visibles
            inputs = driver.find_elements(By.XPATH, "//input")

            input_box = None
            for inp in inputs:
                if inp.is_displayed():
                    input_box = inp
                    break

            if not input_box:
                raise Exception("Champ input introuvable")

            # 🔥 Scroll + focus
            driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
            driver.execute_script("arguments[0].focus();", input_box)

            time.sleep(1)

            # 🔥 Injection JS (ultra fiable)
            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            """, input_box, url_to_test)

            time.sleep(1)

            # 🔍 Trouver bouton cliquable
            buttons = driver.find_elements(By.XPATH, "//button")

            submit_button = None
            for btn in buttons:
                if btn.is_displayed():
                    submit_button = btn
                    break

            if not submit_button:
                raise Exception("Bouton submit introuvable")

            # 🔥 clic JS (contourne tous les blocages)
            driver.execute_script("arguments[0].click();", submit_button)

            # ⏳ attendre changement page (résultat)
            time.sleep(random.uniform(4, 7))

            # 🔁 attendre contenu dynamique
            wait.until(
                lambda d: len(d.find_element(By.TAG_NAME, "body").text) > 50
            )

            # 📄 extraction
            full_html = driver.page_source
            body_text = driver.find_element(By.TAG_NAME, "body").text

            driver.quit()

            return full_html, body_text

        except Exception as e:
            driver.quit()

            if attempt < retries - 1:
                time.sleep(2)
                continue
            else:
                return None, f"Erreur finale: {e}"

# ==============================
# UI STREAMLIT
# ==============================


st.title("🔍 Zscaler Scraper — Version Expert")

url = st.text_input("Saisir une URL à analyser")

if st.button("Analyser"):

    if not url:
        st.warning("Veuillez entrer une URL")
    else:
        with st.spinner("Scraping avancé en cours..."):

            html, text = scrape_zscaler(url)

        if html:
            st.success("Scraping réussi")

            st.subheader("📄 Texte extrait")
            st.text_area("Texte", text, height=300)

            st.subheader("🧾 HTML complet")
            st.code(html, language="html")

        else:
            st.error(text)
