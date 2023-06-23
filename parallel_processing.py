import concurrent.futures

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

# Here pandas as imported so that the dictionaries can be saved as dataframes and final dataframe as excel
import pandas as pd  

# BS4 to parse html and extract content
from bs4 import BeautifulSoup

# Disable all warnings
import warnings
warnings.filterwarnings("ignore")

# Path to the geckodriver executable
geckopath = "./webdriver/geckodriver.exe"

# Empty dataframe to save dictionary after extraction
base_df = pd.DataFrame()

# Selenium 4.x version uses Service class instead of executable_path, and options defined directly
service = Service(executable_path=geckopath)

def coin_overview_extract(link):
    '''
    This function extracts information from a coin's page given a link.
    It follows a specific procedure to extract on-chain and off-chain metrics,
    as well as the summary section of the page.

    Args:
        link (str): The link to the coin's page.

    Returns:
        dict: A dictionary containing the extracted information.
    '''
    # global service
    coin_driver = webdriver.Firefox()
    
    # Define the variables for on-chain and off-chain metrics
    on_chain_vars = {
        'name':'On_chain_',
        'link' :'?tab=on-chain',
        'value_xpath':"/html/body/div[1]/div/div/div[3]/div[3]/div/div[3]/div/div/div[1]/div[1]/h1"        
    }
    off_chain_vars = {        
        'name':'Off_chain_',
        'link' :'?tab=off-chain',
        'value_xpath':"/html/body/div[1]/div/div/div[3]/div[3]/div/div[4]/div/div/div[1]/div[1]/h1"        
    }
    
    wait = WebDriverWait(coin_driver, 15)  # Maximum wait time of 15 seconds for elements/values to load
    element_wait = WebDriverWait(coin_driver,2) # Maximum wait time of 3 seconds for 'show more' to load
    page_dict = {} # Defininig empty dictionary for saving elements
    
    # Iterate over on-chain and off-chain variables    
    for page in [on_chain_vars, off_chain_vars]:
                
        # Load the page
        coin_driver.get(link + page['link'])
        value_xpath = page['value_xpath']
        
        try:
            # Wait for the value to be loaded
            wait.until(EC.presence_of_element_located((By.XPATH, value_xpath)))
        except:
            # If value not present, continue to the next iteration
            off_chain_vars['value_xpath'] = "/html/body/div[1]/div/div/div[3]/div[3]/div/div[3]/div/div/div[1]/div[1]/h1"   
            continue
        
         # Extract the values
        html_source = coin_driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        elements_of_interest = soup.find_all('div', class_='MuiBox-root css-k0t8ss')
        for element in elements_of_interest:
            element_name = page['name'] + element.find('h6', class_="MuiTypography-root MuiTypography-h6 css-huua7q").text
            element_value = element.find('h1', class_="MuiTypography-root MuiTypography-h1 css-r9tpzn").text
            page_dict[element_name] = element_value
 
    # Check if the summary section has a 'show more' indicator, click if present
    try:
        element_xpath = '/html/body/div[1]/div/div/div[3]/div[3]/div/div[1]/div[2]/div[2]/div/div[2]/div[1]/p[2]'
        element_wait.until(EC.presence_of_element_located((By.XPATH,element_xpath)))
        element = coin_driver.find_element("xpath",element_xpath)
        coin_driver.execute_script("arguments[0].click();", element) 
        print("Clicked on show more")      
    except :
        print("No Show More Present")
        pass
    
    # Extract the summary section
    html_source = coin_driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')
    page_dict['summary'] = soup.find('div', class_="MuiBox-root css-1mzx9ln").text
    
    coin_driver.quit()
    return page_dict

def elements_extracted(coin):
    coin_dict = {}
    coin_name = coin.find('p', class_='MuiTypography-root MuiTypography-body1 css-xmxusp').text
        
    coin_type_all, coin_tags_all, coin_governs_all =  coin.find_all('td', class_='MesTableCell-alignLeft MesTableCell-colorPrimary css-z1fs94')
    
    coin_type = []
    for type in coin_type_all:
        coin_type.append(type.text)
    
    coin_tag = []
    for tag in coin_tags_all:
        coin_tag.append(tag.text)
        
    coin_page_link = "https://messari.io" + coin.find('a', class_="MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways css-7zr2gf")['href']
    coin_dict['coin_name'] = coin_name
    coin_dict['coin_type'] = coin_type
    coin_dict['coin_tag'] = coin_tag
    coin_dict['coin_page_link'] = coin_page_link
    
    # Extract on-chain and off-chain metrics using the coin_overview_extract function
    coin_dict.update(coin_overview_extract(coin_page_link))
    
    return coin_name, coin_dict

def process_coin(coin):
    coin_name, coin_dict = elements_extracted(coin)
    return coin_name, coin_dict


def summary_page(page_number):
    '''
    Extracts coin details from the summary page and saves them in a DataFrame.

    Args:
        page_number (int): The page number of the summary page to extract coins from.

    Returns:
        None
    '''
    global i
    global base_df
    
    # global service
    driver = webdriver.Firefox()
    
    # Construct the URL of the summary page
    master_page = f'https://messari.io/governor/daos?page={page_number}'
    
     # Open the summary page
    driver.get(master_page)

    # Wait for coins to be loaded
    wait = WebDriverWait(driver, 20)  # Maximum wait time of 20 seconds
    coin_xpath = "/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div[4]/div/div[2]/div/div[2]/div[1]/div/div[1]/table/tbody/tr[1]/td[1]/a/p"
    wait.until(EC.presence_of_element_located((By.XPATH, coin_xpath)))

    soup = BeautifulSoup(driver.page_source,'html.parser')

    coins = soup.find('tbody',class_='css-0').find_all('tr', class_='css-6waxvc')
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        
        futures = [executor.submit(process_coin, coin) for coin in coins]
        
        for future in concurrent.futures.as_completed(futures):
            coin_name, coin_dict = future.result()
            print(coin_name,"\n","*"*20,coin_dict)
            
            # Create a temporary DataFrame with the coin detail
            temp_df = pd.DataFrame([coin_dict], index=[0])
            
            # Concatenate the temporary DataFrame with the base DataFrame
            base_df = pd.concat([base_df,temp_df], ignore_index=True)
            
            # Print the current state of the base DataFrame
            print(base_df)
            
            # Save the base DataFrame as an Excel file
            base_df.to_excel(f'output_page_{page_number}.xlsx', sheet_name='Extract')
            
        concurrent.futures.wait(futures)

 
    


summary_page(1)





