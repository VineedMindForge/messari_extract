from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import pandas as pd 

from bs4 import BeautifulSoup

# Path to the geckodriver executable
geckopath = "./webdriver/geckodriver.exe"

i=0
base_df = pd.DataFrame()


# Create a Firefox profile with pop-up blocking
profile = FirefoxProfile()
profile.set_preference('dom.disable_beforeunload', True)
profile.set_preference('browser.popups.showPopupBlocker', False)

# Configure Firefox options
options = Options()
options.profile = profile

service = Service(executable_path=geckopath, options=options)

# Create a Firefox WebDriver instance with configured options
global driver
driver = webdriver.Firefox(service=service)

summary_coin = pd.DataFrame()
i=0

def coin_overview_extract(link):
    
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
    
    wait = WebDriverWait(driver, 30)  # Maximum wait time of 30 seconds
    page_dict = {}
    for page in [on_chain_vars, off_chain_vars]:
        
        driver.get(link + page['link'])
        value_xpath = page['value_xpath']
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, value_xpath)))
        except:
            off_chain_vars['value_xpath'] = "/html/body/div[1]/div/div/div[3]/div[3]/div/div[3]/div/div/div[1]/div[1]/h1"   
            continue
        
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        
        elements_of_interest = soup.find_all('div', class_='MuiBox-root css-k0t8ss')
        for element in elements_of_interest:
            element_name = page['name'] + element.find('h6', class_="MuiTypography-root MuiTypography-h6 css-huua7q").text
            element_value = element.find('h1', class_="MuiTypography-root MuiTypography-h1 css-r9tpzn").text
            page_dict[element_name] = element_value
 
     # If the summary has a 'show more' indicator, then that is clicked so that summary is extracted completely
    try:
        element = driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div[3]/div/div[1]/div[2]/div[2]/div/div[2]/div[1]/p[2]')
        driver.execute_script("arguments[0].click();", element)
    except:
        pass
    
    # All source code saved and parsed by BS4
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')

    page_dict['summary'] = soup.find('div', class_="MuiBox-root css-1mzx9ln").text
    return page_dict



def summary_page(page_number):
    global i
    global base_df
    master_page = f'https://messari.io/governor/daos?page={page_number}'
    
    driver.get(master_page)

    wait = WebDriverWait(driver, 20)  # Maximum wait time of 10 seconds
    coin_xpath = "/html/body/div[1]/div/div/div[3]/div/div[2]/div[1]/div[4]/div/div[2]/div/div[2]/div[1]/div/div[1]/table/tbody/tr[1]/td[1]/a/p"
    wait.until(EC.presence_of_element_located((By.XPATH, coin_xpath)))

    soup = BeautifulSoup(driver.page_source,'html.parser')

    for coin in soup.find('tbody',class_='css-0').find_all('tr', class_='css-6waxvc'):
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
        coin_dict.update(coin_overview_extract(coin_page_link))
    
    
        temp_df = pd.DataFrame([coin_dict], index=[0])
        base_df = pd.concat([base_df,temp_df], ignore_index=True)
        print(base_df)
        base_df.to_excel('output2.xlsx', sheet_name='Sample')
        # i+=1
        # if i==10:
        #     break
        
        # print(f"Coin Name - {coin_name}")
        # print(f"Coin Types - {coin_type_all.text}, Coin Tags - {coin_tags_all.text} ")
        
        
for i in range (2,9):
    summary_page(i)


        
    
