from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time, os

import concurrent.futures

import pandas as pd

from bs4 import BeautifulSoup

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
        list: A list of name and links retrieved from the second column, excluding the first row.

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
        name = row[0]
        proposal_link = row[1] + '/proposals'
        link_list.append([name,proposal_link])

    # Close the workbook
    wb.close()
    print("All links to the coin's proposal main  page retrieved")

    return link_list

def close_overlay(driver):
    wait = WebDriverWait(driver, 10)
    button = "/html/body/div[2]/div[3]/div/div[1]/div/button"
    
    try:
        overlay_window = wait.until(EC.visibility_of_element_located((By.XPATH, button)))
        driver.execute_script("arguments[0].click();", overlay_window)
        print("Overlay window closed")
    except:
        pass
    
    return
  
def perform_infinite_scroll_retrieve_code(link):
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
        close_overlay(driver)

        # Scroll to the bottom of the page
        elements = driver.find_elements(By.CLASS_NAME,"MuiTableRow-root")
        initial_count = len(elements)
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
    
    html_code = driver.page_source
    driver.quit()
    print("Page closed")
    
    return html_code, BeautifulSoup(html_code, 'html.parser')

def set_prelim_vote_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    date = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]").text
    sentiments = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
    row['prelim_sentiments'] = sentiments
    prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
    # print(prem_other_details)
    elements = prem_other_details.split(" by ")
    element1 = elements[0]
    element2 = elements[1].split(" on ")[0]
    element3 = elements[1].split(" on ")[1]
    row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    driver.quit()
    
    return row
    
def set_off_chain_active_vote_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
    row['off_chain_author'] = key_info_elements[0].text.replace('Author',"")
    row['off_chain_start_date'] = key_info_elements[5].text
    row['off_chain_end_date'] = key_info_elements[6].text
    #Preliminary discussion
    try:
        row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
        prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
        # print(prem_other_details)
        elements = prem_other_details.split(" by ")
        element1 = elements[0]
        element2 = elements[1].split(" on ")[0]
        element3 = elements[1].split(" on ")[1]
        row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    except:
        pass
    off_chain_votes = soup.select(".css-1s50f5r")[-1]
    off_chain_option_list = off_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","").split("%")[:-1]
    option_dict = {}
    for index, option in enumerate(off_chain_option_list, start=1):
        option_dict[f"Off_Chain_Option_{index}"] = option
        
    option_dict = pd.Series(option_dict)
    row = pd.concat([row,option_dict])
    driver.quit() 
    return row

def set_off_chain_remaining_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
    row['off_chain_author'] = key_info_elements[0].text.replace('Author',"")
    row['off_chain_start_date'] = key_info_elements[5].text
    row['off_chain_end_date'] = key_info_elements[6].text
    #Preliminary discussion
    try:
        row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
        prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
        # print(prem_other_details)
        elements = prem_other_details.split(" by ")
        element1 = elements[0]
        element2 = elements[1].split(" on ")[0]
        element3 = elements[1].split(" on ")[1]
        row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    except:
        pass
    
    off_chain_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1) div")[0]        
    off_chain_option_list = [f"{element}%" for element in off_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","").split("%")][:-1]
    option_dict = {}
    for index, option in enumerate(off_chain_option_list, start=1):
        option_dict[f"Off_Chain_Option_{index}"] = option
        
    option_dict = pd.Series(option_dict)
    row = pd.concat([row,option_dict])
    driver.quit() 
    return row       

def set_temp_check_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
    row['temp_check_author'] = key_info_elements[0].text.replace('Author',"")
    row['temp_check_start_date'] = key_info_elements[5].text
    row['temp_check_end_date'] = key_info_elements[6].text
    #Preliminary discussion
    try:
        row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
        prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
        # print(prem_other_details)
        elements = prem_other_details.split(" by ")
        element1 = elements[0]
        element2 = elements[1].split(" on ")[0]
        element3 = elements[1].split(" on ")[1]
        row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    except:
        pass
    temp_check_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1)")[0]
    temp_check_option_list = [f"{element}%" for element in temp_check_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
        .replace('Results',"").split("%")][:-1]
    option_dict = {}
    for index, option in enumerate(temp_check_option_list, start=1):
        option_dict[f"temp_check_Option_{index}"] = option
        
    option_dict = pd.Series(option_dict)
    row = pd.concat([row,option_dict])
    driver.quit() 
    return row       

def set_on_chain_active_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    
    # Check if off-chain also present
    try:
        top_boxes = len(soup.find('div', class_="MuiBox-root css-1qoa196").find_all('div', class_=lambda value: value and value.startswith("MuiPaper-root MuiPaper-elevation")))
        off_chain_present = False if top_boxes == 2 else True
    except:
        off_chain_present = False
    
    row['on_chain_author'] = soup.find_all('div', 'MuiBox-root css-z53l98')[0].text.replace('Author',"")
    row['on_chain_start_date'] = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[1].text.replace("ACTIVE VOTE","")
    row['on_chain_end_date'] = soup.find('div', class_= "MuiContainer-root MuiContainer-maxWidthMd css-1u2mkel").find('div', class_ = "MuiBox-root css-1isemmb").text
    #Preliminary discussion
    try:
        row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
        prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
        # print(prem_other_details)
        elements = prem_other_details.split(" by ")
        element1 = elements[0]
        element2 = elements[1].split(" on ")[0]
        element3 = elements[1].split(" on ")[1]
        row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    except:
        pass
    
    # Adding on-chain votes
    on_chain_votes = soup.select(".css-1s50f5r+ .css-1s50f5r")[0]
    on_chain_option_list = [f"{element}%" for element in on_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
        .replace('Results',"").split("%")][:-1]
    option_dict = {}
    for index, option in enumerate(on_chain_option_list, start=1):
        option_dict[f"on_chain_Option_{index}"] = option
            
    option_dict = pd.Series(option_dict)
    row = pd.concat([row,option_dict])
    driver.quit() 
    return row 

def set_on_chain_remaining_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    
    # Check if off-chain also present
    try:
        top_boxes = len(soup.find('div', class_="MuiBox-root css-1qoa196").find_all('div', class_=lambda value: value and value.startswith("MuiPaper-root MuiPaper-elevation")))
        off_chain_present = False if top_boxes == 2 else True
    except:
        off_chain_present = False
        
    row['on_chain_author'] = soup.find_all('div', 'MuiBox-root css-z53l98')[0].text.replace('Author',"")
    row['on_chain_start_date'] = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[3].text
    row['on_chain_end_date'] = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[4].text
    #Preliminary discussion
    try:
        row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
        prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
        # print(prem_other_details)
        elements = prem_other_details.split(" by ")
        element1 = elements[0]
        element2 = elements[1].split(" on ")[0]
        element3 = elements[1].split(" on ")[1]
        row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    except:
        pass
    
    # Adding on-chain votes
    on_chain_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1)")[0]
    on_chain_option_list = [f"{element}%" for element in on_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
        .replace('Results',"").split("%")][:-1]
    option_dict = {}
    for index, option in enumerate(on_chain_option_list, start=1):
        option_dict[f"on_chain_Option_{index}"] = option
            
    option_dict = pd.Series(option_dict)
    row = pd.concat([row,option_dict])
    
    #off chain elements extract 
    if off_chain_present:            
        key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
        row['off_chain_author'] = key_info_elements[3].text.replace('Author',"")
        row['off_chain_start_date'] = key_info_elements[8].text
        row['off_chain_end_date'] = key_info_elements[9].text
        off_chain_votes = soup.select(".css-h5fkc8+ .css-178yklu .css-15j76c0:nth-child(1)")[0]
        off_chain_option_list = [f"{element}%" for element in off_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
            .replace('Results',"").split("%")][:-1]
        option_dict = {}
        for index, option in enumerate(off_chain_option_list, start=1):
            option_dict[f"Off_Chain_Option_{index}"] = option
            
        option_dict = pd.Series(option_dict)
        row = pd.concat([row,option_dict])
    
    driver.quit()
    return row
    
def set_on_chain_failed_extract(row, html, soup):
    link = row['Links']
    driver = webdriver.Firefox()        
    driver.get(link)
    time.sleep(10)
    close_overlay(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    summary = soup.find('div', class_="MuiBox-root css-79elbk").text
    row['summary'] = summary
    
    # Check if off-chain also present
    prelim_discussion_present = True
    try:
        top_boxes = len(soup.find('div', class_="MuiBox-root css-1qoa196").find_all('div', class_=lambda value: value and value.startswith("MuiPaper-root MuiPaper-elevation")))
        off_chain_present = False if top_boxes == 2 else True
    except:
        off_chain_present = False
        prelim_discussion_present = False
    
    row['on_chain_author'] = soup.find_all('div', 'MuiBox-root css-z53l98')[0].text.replace('Author',"")
    row['on_chain_start_date'] = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[4].text
    row['on_chain_end_date'] = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[5].text
    #Preliminary discussion
    try:
        row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
        prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
        # print(prem_other_details)
        elements = prem_other_details.split(" by ")
        element1 = elements[0]
        element2 = elements[1].split(" on ")[0]
        element3 = elements[1].split(" on ")[1]
        row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
    except:
        pass
    
    # Adding on-chain votes
    on_chain_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1)")[0]
    on_chain_option_list = [f"{element}%" for element in on_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
        .replace('Results',"").split("%")][:-1]
    option_dict = {}
    for index, option in enumerate(on_chain_option_list, start=1):
        option_dict[f"on_chain_Option_{index}"] = option
            
    option_dict = pd.Series(option_dict)
    row = pd.concat([row,option_dict])
    
    #off chain elements extract 
    if off_chain_present:            
        key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
        row['off_chain_author'] = key_info_elements[3].text.replace('Author',"")
        row['off_chain_start_date'] = key_info_elements[8].text
        row['off_chain_end_date'] = key_info_elements[9].text
        off_chain_votes = soup.select(".css-h5fkc8+ .css-178yklu .css-15j76c0:nth-child(1)")[0]
        off_chain_option_list = [f"{element}%" for element in off_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
            .replace('Results',"").split("%")][:-1]
        option_dict = {}
        for index, option in enumerate(off_chain_option_list, start=1):
            option_dict[f"Off_Chain_Option_{index}"] = option
            
        option_dict = pd.Series(option_dict)
        row = pd.concat([row,option_dict])    
    
    
    
    driver.quit() 
    return row 

def function_for_threading(data):
    result, row, index, name = data
    stage = row['Stage']
    status = row['Status']
    # print(f"Index{index}*** {stage}*** {status} processing. {row['Proposal']}***")
    
    try:
            
        if stage == 'Preliminary Discussion':
            updated_row = set_prelim_vote_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
        elif stage =='Off-Chain Vote' and status in ['Active Vote','Canceled']:
            updated_row = set_off_chain_active_vote_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
        elif stage =='Off-Chain Vote' and status in ['Succeeded','Failed']:
            updated_row = set_off_chain_remaining_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
       
        elif stage == 'Temperature Check' and status in ['Succeeded','Failed']:
            updated_row = set_temp_check_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
                    
        elif stage =="On-Chain Vote" and status == "Active Vote":
            updated_row = set_on_chain_active_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
        elif stage =="On-Chain Vote" and status in ["Canceled", "Executed"]:
            updated_row = set_on_chain_remaining_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
        elif stage =="On-Chain Vote" and status in ["Failed"]:
            updated_row = set_on_chain_failed_extract(row, html, soup)
            for feature, value in updated_row.items():
                result.loc[index, feature] = value
        else:
            print(f"Use-Case Not Defined {row['Proposal']}. Stage - {stage}, Status - {status}")        
    
    except:
        print(f"Error - {row['Proposal']}. Need to check. Stage - {stage}, Status - {status}")
                
    result.to_excel(f"./proposal_extract/{name}.xlsx")
    
def update_set_wise_details(result, name):
    # for index, row in result.iterrows():
    #     data = [result, row, index]
    #     function_for_threading(data)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        data = [(result, row, index, name) for index, row in result.iterrows()]
        executor.map(function_for_threading, data)

def detailed_proposal_extract(html, soup, name):
    df = pd.read_html(html)[1]
    
    table_row = soup.find_all('tr', class_ = "MuiTableRow-root css-93kbmv")
    links_column = pd.Series(dtype="object")
    for row in table_row:
        link_element = row.find('a')['href']
        link = "https://messari.io/" + link_element
        # print(link)
        links_column= pd.concat([links_column,pd.Series(link)])   
        
    links_column.name = "Links"
    table = df.reset_index(drop=True)
    links_column = links_column.reset_index(drop=True)
    
    split_proposal = table['Proposal'].str.split("•", expand=True)
    split_proposal.columns = ['Proposal', 'Creation_date', 'Stage']
    result = pd.concat([split_proposal,table.drop('Proposal', axis=1),links_column], axis=1)
    
    result.to_excel(f"./proposal_extract/{name}.xlsx")
    update_set_wise_details(result, name)
    print(f"Complete extract done for {name} coin. Moving to next coin")
  


folder_path = "./data_extracts/"
extract_path = "./proposal_extract/"
file_name = 'output_page_consolidated_1to8.xlsx'  # Replace with the actual file path
sheet_name = 'proposal_extract_list'  # Replace with the actual sheet name
link_list = retrieve_link_list(os.path.join(folder_path,file_name), sheet_name) 

os.makedirs(extract_path) if not os.path.exists(extract_path) else None
  
    
for [name, link] in link_list[5:10]:
    html, soup = perform_infinite_scroll_retrieve_code(link)
    detailed_proposal_extract(html, soup, name)








