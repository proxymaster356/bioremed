import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


STATE_NAME = "WEST BENGAL"
DISTRICT_NAME = "PASCHIM BARDHAMAN"
PARAMETER_SUFFIX = "_N"
OUTPUT_FILE = "paschim_bardhaman_soil_data.csv"
URL = "https://soilhealth.dac.gov.in/slusi-visualisation/"


def click_labeled_combobox(label_text: str, target_text: str) -> None:
    index_map = {"State": 0, "District": 1}
    combobox_index = index_map.get(label_text, 0)
    combobox = WebDriverWait(driver, 20).until(
        lambda current_driver: (
            current_driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")[combobox_index]
            if len(current_driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")) > combobox_index
            else None
        )
    )
    driver.execute_script(
        """
        const element = arguments[0];
        const value = arguments[1];
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        element.focus();
        nativeInputValueSetter.call(element, value);
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        combobox,
        target_text,
    )
    option_xpath = f"//li[@role='option' and normalize-space()='{target_text}']"
    option = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, option_xpath))
    )
    driver.execute_script("arguments[0].click();", option)
    time.sleep(1.5)


def click_radio_suffix(suffix: str) -> None:
    radio = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"input[type='radio'][value$='{suffix}']"))
    )
    driver.execute_script("arguments[0].click();", radio)
    time.sleep(2)


options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.get(URL)

try:
    click_labeled_combobox("State", STATE_NAME)
    click_labeled_combobox("District", DISTRICT_NAME)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"input[type='radio'][value$='{PARAMETER_SUFFIX}']"))
    )
    click_radio_suffix(PARAMETER_SUFFIX)

    row_xpath_candidates = [
        "//table[@id='soilDataTable']/tbody/tr",
        "//table//tbody/tr",
        "//*[@role='table']//tr[@role='row']",
        "//*[@role='table']//tr",
    ]

    rows = []
    for locator in row_xpath_candidates:
        rows = driver.find_elements(By.XPATH, locator)
        if rows:
            break

    data = []
    for row in rows:
        columns = [cell.text.strip() for cell in row.find_elements(By.TAG_NAME, "td")]
        if columns:
            data.append(columns)

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Scraping completed: {OUTPUT_FILE} ({len(df)} rows)")

finally:
    driver.quit()
