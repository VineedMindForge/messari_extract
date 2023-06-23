from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time

#Ignore all warnings
import warnings
warnings.filterwarnings('ignore')

# Library to accessa nd work with excel
import openpyxl

def retrieve_link_list(file_path, sheet_name):
    """
    Retrieve a list of links from the second column of an Excel file, excluding the first row.

    Args:
        file_path (str): The path of the Excel file.
        sheet_name (str): The name of the sheet containing the data.

    Returns:
        list: A list of links retrieved from the second column, excluding the first row.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        openpyxl.utils.exceptions.InvalidFileException: If the specified file is not a valid Excel file.
        KeyError: If the specified sheet name does not exist in the Excel file.
    """

    # Load the workbook
    try:
        wb = openpyxl.load_workbook(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    except openpyxl.utils.exceptions.InvalidFileException:
        raise openpyxl.utils.exceptions.InvalidFileException(f"The file '{file_path}' is not a valid Excel file.")

    # Access the sheet
    try:
        sheet = wb[sheet_name]
    except KeyError:
        raise KeyError(f"The sheet '{sheet_name}' does not exist in the Excel file.")

    link_list = []

    # Iterate over rows and retrieve the links from the second column
    for row in sheet.iter_rows(min_row=2, values_only=True):
        proposal_link = row[1] + '/proposals'
        link_list.append(proposal_link)

    # Close the workbook
    wb.close()

    return link_list

file_path = './data_extracts/output_page_consolidated_1to8.xlsx'  # Replace with the actual file path
sheet_name = 'proposal_extract_list'  # Replace with the actual sheet name

link_list = retrieve_link_list(file_path, sheet_name)
print(link_list)


def perform_infinite_scroll(link):
    """
    Open the Firefox browser, perform infinite scroll, and wait until the page loads completely.

    Args:
        link (str): The URL of the web page to scroll.

    Raises:
        TimeoutException: If the page loading times out.
    """

    # Set Firefox options
    options = Options()
    options.headless = False  # Set to True to run Firefox in headless mode

    # Create Firefox driver
    driver = webdriver.Firefox(options=options)

    try:
        # Open the web page
        driver.get(link)

        # Wait for the page to load completely
        time.sleep(5)

        # Scroll to the bottom of the page
        elements = driver.find_elements(By.CLASS_NAME,"MuiTableRow-root")
        initial_count = len(elements)
        print(initial_count)
        while True:
            last_element = elements[-1]
            driver.execute_script("arguments[0].scrollIntoView();", last_element)
            time.sleep(5)
            elements = driver.find_elements(By.CLASS_NAME,"MuiTableRow-root")
            current_count = len(elements)
            if current_count == initial_count:
                try:
                    button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[3]/div[2]/div[2]/div[3]/button")
                    if button.is_displayed():
                        button.click()
                        continue
                except:
                    pass
                    
                break
            initial_count = current_count

    except TimeoutException:
        print("Page loading timed out.")

    

# Example usage
for link in link_list:
    perform_infinite_scroll(link)








