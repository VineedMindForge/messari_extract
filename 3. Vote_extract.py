import os, time, bs4
import concurrent.futures 
from pathlib import Path
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
    
def process_rows(inputs):
    votes_extract_folder_path, file, index, row = inputs
    link = row['Links']
    stage = row['Stage']
    coin = file
    
    if stage =="Preliminary Discussion":
        return
    
    button_text = []
    
    # Open webpage using Selenium
    driver = webdriver.Firefox()  # Assuming you're using Chrome WebDriver
    driver.get(link)
    time.sleep(10)
    
    wait = WebDriverWait(driver, 10)
    
        
    elements = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,'.css-topwlp')))
    soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

    top_boxes = soup.find('div', class_="MuiBox-root css-1qoa196").find_all('div', class_=lambda x: x and x.startswith('MuiPaper-root MuiPaper-elevation MuiPaper-rounded MuiPaper-elevation0 MuiCard-root jss'))
    vote_names = []
    for box in top_boxes:
        vote_names.append(box.find("h6").text)
    print(vote_names)

    button_text = []
    votes_data = []

    for _ in range(len(elements)):
        
        driver.get(link)
        time.sleep(10)
        buttons = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,'.css-topwlp')))
        for button in buttons:  
            if button.text.startswith("VIEW ALL") and button.text not in button_text:
                button_text.append(button.text)
                # print(f"Found button {button.text.strip()}")
                driver.execute_script("arguments[0].click();", button)
                count_clicker = 0
                try:
                    while count_clicker<10:
                        
                        time.sleep(4)
                        load_more_button_css = ".MuiButton-outlined"
                        load_more_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, load_more_button_css)))
                        driver.execute_script("arguments[0].click();", load_more_button)
                        count_clicker+=1
                        
                except:
                    pass
                
                finally:
                    votes_data.append(pd.read_html(driver.page_source)[-1])
    
    
    driver.quit()        
    try:        
        
        for i in range(1,len(vote_names)):
            file_name = f"{coin}_{index}_{row['Proposal']}_{vote_names[i]}.xlsx"
            full_path = votes_extract_folder_path / file_name
            votes_data[-i].to_excel(full_path,index=False)
    except:
        print(f"{coin}_{index}_{row['Proposal']} Some Error", "*"*20)

# Function to iterate through DataFrame rows and process links concurrently 
def process_rows_concurrently(df, max_workers,file,votes_extract_folder_path):
    # Create a ThreadPoolExecutor with the specified max_workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks for each row in the DataFrame
        futures = [executor.submit(process_rows,[votes_extract_folder_path, file, index, row]) for index, row in df.iterrows()]
        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

       
    
    
    
# Set the folder path to scan
proposal_folder_path = './proposal_extract'

# Set the folder path for votes extract
votes_extract_folder_path = Path(proposal_folder_path + '/votes_extract')
votes_extract_folder_path.mkdir(parents=True, exist_ok=True)

# Get a list of all XLSX files in the folder
coin_files = [f for f in os.listdir(proposal_folder_path) if f.endswith('.xlsx')]

# Iterate through each XLSX file
for file in coin_files:
    file_path = os.path.join(proposal_folder_path, file)
    
    # Convert Excel file to DataFrame
    df = pd.read_excel(file_path)
    
    
    max_workers = 5
    process_rows_concurrently(df, max_workers,file,votes_extract_folder_path)
    
    
    # Iterate through each row
    for index, row in df.iterrows():
        process_rows([votes_extract_folder_path,file,index,row])
    
    print("@*"*20, file," completed")
