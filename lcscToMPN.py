import requests
from bs4 import BeautifulSoup
import time

import requests
from bs4 import BeautifulSoup
from tkinter import Tk, filedialog


import re

def try_parse_int(text):
    try:
        return int(text.replace(",", "").strip())
    except:
        return 0

def extract_table_details_from_soup_v2(soup):
    pricing_breaks, unit_prices = [], []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if headers == ['Qty.', 'Unit Price', 'Ext. Price']:
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    qty_span = cells[0].find("span")
                    price_span = cells[1].find("span")
                    if qty_span and price_span:
                        try:
                            qty = int(qty_span.get_text(strip=True).replace(",", "").replace("+", ""))
                            price = float(price_span.get_text(strip=True).replace("$", ""))
                            pricing_breaks.append(qty)
                            unit_prices.append(price)
                        except ValueError:
                            continue
    quantity_available = None
    qty_div = soup.find("div", string=re.compile("Can Ship Immediately", re.I))
    if qty_div:
        parent = qty_div.find_parent("div")
        if parent:
            match = re.search(r'([\d,]+)', parent.text)
            if match:
                quantity_available = int(match.group(1).replace(",", ""))
    return {
        "Quantity Available": quantity_available,
        "Pricing Breaks": pricing_breaks,
        "Unit Prices": unit_prices,
        "qty":qty,
        "price":price,
        "pricing_breaks":pricing_breaks,
        "unit_prices":unit_prices
    }

def extract_parameters_from_any_table(soup):
    params = {
        "Minimum Purchase Quantity": 0,
        "Ordering Multiple": 0,
        "Standard Packaging": 0,
        "Sales Unit": "Pieces"
    }
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) != 2:
                continue
            label = tds[0].get_text(strip=True)
            value = tds[1].get_text(strip=True).replace(",", "")
            if label in params:
                if label == "Sales Unit":
                    params[label] = value
                else:
                    try:
                        params[label] = int(value)
                    except ValueError:
                        pass
    return params

def extract_all_lcsc_details(soup):
    price_data = extract_table_details_from_soup_v2(soup)
    param_data = extract_parameters_from_any_table(soup)
    price_data.update(param_data)
    return price_data

def get_LCSC_info(lcsc_part,_debug=False):
    url = f"https://www.lcsc.com/product-detail/{lcsc_part}.html"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {lcsc_part}: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        return extract_all_lcsc_details(soup)
    
    except Exception as e:
        print(f"Error fetching {lcsc_part}: {e}")
        return None

def get_manufacturer_info(lcsc_part,_debug=False):
    url = f"https://www.lcsc.com/product-detail/{lcsc_part}.html"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {lcsc_part}: HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        if _debug:
            # Prompt user to save debug output with default name = LCSC part number
            root = Tk()
            root.withdraw()  # Hide the tkinter root window
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="Save debug soup content as",
                initialfile=f"{lcsc_part}.txt"
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(soup.prettify())
                print(f"Saved debug output to {save_path}")
            else:
                print("Save canceled.")

        # Extract Manufacturer Part Number from <meta name="description">
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and " by " in meta_desc["content"]:
            mpn_value = meta_desc["content"].split(" by ")[0].strip()
        else:
            mpn_value = "Not Found"

        # Extract Manufacturer from <meta name="og:product:brand">
        meta_brand = soup.find("meta", attrs={"name": "og:product:brand"})
        mfg_value = meta_brand["content"].strip() if meta_brand else "Not Found"

        return {
            'LCSC Part': lcsc_part,
            'Manufacturer': mfg_value,
            'MPN': mpn_value
        }

    except Exception as e:
        print(f"Error fetching {lcsc_part}: {e}")
        return None



# === Example usage ===
lcsc_parts = [
    "C23138",
    "C23630",
    "C125116",
    "C21190",
    "C840096"
]

for part in lcsc_parts:
    info = get_LCSC_info(part)
    if info:
        print(info)
    time.sleep(1)  # Be polite and don’t hammer their servers