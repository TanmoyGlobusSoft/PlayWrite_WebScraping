import os
import json
import urllib.parse
from playwright.sync_api import sync_playwright


def main():
    url = "https://www.amazon.in/Lenovo-IdeaPad-Next-Gen-Keyboard-83UR009QIN/dp/B0H3PV7418/?_encoding=UTF8&ref_=pd_hp_d_atf_dealz_cs"
    abs_path = os.path.abspath(__file__)  # f:\Learning\PlayWrite\AI Code\main.py
    dir_name = os.path.dirname(abs_path)  # f:\Learning\PlayWrite\AI Code
    output_dir = os.path.join(dir_name, "output")  # f:\Learning\PlayWrite\AI Code\output
    
    # os.makedirs() → Creates the directory
    # exist_ok=True → Don't raise an error if the directory already exists.
    os.makedirs(output_dir, exist_ok = True)


main()
