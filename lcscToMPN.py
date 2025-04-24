import requests
from bs4 import BeautifulSoup
import time

import requests
from bs4 import BeautifulSoup
from tkinter import Tk, filedialog

def get_manufacturer_info(lcsc_part):
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
    info = get_manufacturer_info(part)
    if info:
        print(info)
    time.sleep(1)  # Be polite and don’t hammer their servers