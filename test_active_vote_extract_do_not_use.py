from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time

import pandas as pd

from bs4 import BeautifulSoup


# list_of_urls = [ #on-chain active / (on chain/off chain combineed)
#     'https://messari.io//governor/proposal/c9eaf0a3-9bbe-4d7f-9dd8-ec782ffdae0b?daoSlug=aave-governance&daoTab=proposals',
#       'https://messari.io//governor/proposal/c6ad38f1-bd8c-406c-a30f-8f36341066a1?daoSlug=aave-governance&daoTab=proposals'

# ]

# list_of_urls = [ #on-chain Executed (onchain off chain combined)
#     'https://messari.io//governor/proposal/8d227b4e-1239-4bfd-9e69-eac381357f64?daoSlug=aave-governance&daoTab=proposals',
# 'https://messari.io//governor/proposal/1062ee0d-dcbc-453f-a8b1-f5b765d34a74?daoSlug=aave-governance&daoTab=proposals',
# 'https://messari.io//governor/proposal/cd4719d9-39b1-4ee1-b7e6-a7ceb260a581?daoSlug=aave-governance&daoTab=proposals',
# 'https://messari.io//governor/proposal/7472ef91-b7ca-42e2-81e0-68876e8ac4ab?daoSlug=aave-governance&daoTab=proposals',
# 'https://messari.io/governor/proposal/778e3931-73c8-43da-a5ad-4cc0571593d0?daoSlug=aave-governance&daoTab=proposals'

# ]

list_of_urls = [ #on-chain failed (onchain off chain combined)
    'https://messari.io//governor/proposal/75b2e335-129d-4938-885e-dda204bc0a29?daoSlug=aave-governance&daoTab=proposals',
'https://messari.io//governor/proposal/8b48c9ce-7bd3-4a05-89b1-db4fce2190e2?daoSlug=aave-governance&daoTab=proposals',
'https://messari.io//governor/proposal/9084cd81-7716-4f8c-9ec3-2f3597433edd?daoSlug=aave-governance&daoTab=proposals',
'https://messari.io//governor/proposal/ad10ee9e-12c6-4af1-a384-3afad02bab0c?daoSlug=aave-governance&daoTab=proposals',
'https://messari.io//governor/proposal/90965240-1fef-4c6d-9941-e4653bb47215?daoSlug=aave-governance&daoTab=proposals'

]

# list_of_urls = [ 
#         'https://messari.io//governor/proposal/d252e1ed-e693-4b00-b97d-0ce8528126cc?daoSlug=aave-governance&daoTab=proposals',
#         'https://messari.io//governor/proposal/09993c2f-5325-4130-ae70-e1857e992912?daoSlug=aave-governance&daoTab=proposals'         
# ]




# for index, url in enumerate(list_of_urls, start=1):
#     driver = webdriver.Firefox()
#     driver.get(url)
#     time.sleep(5)
#     content = driver.page_source
#     with open(f'html\html{index}.txt', 'w') as file:
#         file.write(content)
#     print(f"HTML of {index} saved")
#     driver.quit()

import os 

file_list = os.listdir('./html')

file_contents = {}

for file_name in file_list:
    if file_name.endswith('.txt'):
        file_path = os.path.join("./html", file_name)
        
    with open(file_path, 'r') as file:
        content = file.read()
        file_contents[file_name] = content

for file, content in file_contents.items():
    soup = BeautifulSoup(content, 'html.parser')
    summary= soup.find('div', class_="MuiBox-root css-79elbk").text
    print(file, "--->")
    # print(summary)
    
    prelim_discussion_present = True
    try:
        top_boxes = len(soup.find('div', class_="MuiBox-root css-1qoa196").find_all('div', class_=lambda value: value and value.startswith("MuiPaper-root MuiPaper-elevation")))
        off_chain_present = False if top_boxes == 2 else True
    except:
        off_chain_present = False
        prelim_discussion_present = False
    # print(off_chain_present)
    on_chain_author = soup.find_all('div', 'MuiBox-root css-z53l98')[0].text.replace('Author',"")
    on_chain_start_date = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[4].text
    on_chain_end_date = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[5].text
    # print(on_chain_author)
    # print(on_chain_start_date)
    # print(on_chain_end_date)
    
    on_chain_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1)")[0]
    on_chain_option_list = [f"{element}%" for element in on_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
        .replace('Results',"").split("%")][:-1]
    option_dict = {}
    for index, option in enumerate(on_chain_option_list, start=1):
        option_dict[f"on_chain_Option_{index}"] = option
    
    # print(option_dict)
    
    
    #off chain elements extract 
    if off_chain_present:  
        key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
        off_chain_author = key_info_elements[3].text.replace('Author',"")
        off_chain_start_date = key_info_elements[8].text
        off_chain_end_date = key_info_elements[9].text
        # print(off_chain_author,off_chain_start_date,off_chain_end_date)
        # for element in key_info_elements:
        #     print(element.text, end='*'*5)
        # print()
        off_chain_votes = soup.select(".css-h5fkc8+ .css-178yklu .css-15j76c0:nth-child(1)")[0]
        off_chain_option_list = [f"{element}%" for element in off_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
            .replace('Results',"").split("%")][:-1]
        option_dict = {}
        for index, option in enumerate(off_chain_option_list, start=1):
            option_dict[f"Off_Chain_Option_{index}"] = option
        # print(option_dict)
        
    # Preliminary discussion
    prelim_sentiments = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
    print(prelim_sentiments)
    prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
    # print(prem_other_details)
    elements = prem_other_details.split(" by ")
    element1 = elements[0]
    element2 = elements[1].split(" on ")[0]
    element3 = elements[1].split(" on ")[1]
    prelim_bottom_date, prelim_author, prelim_location = [element1, element2, element3]
    print(prelim_bottom_date, prelim_author, prelim_location)

        
#     print()
#     # off_chain_author = key_info_elements[0].text.replace('Author',"")
#     # print(off_chain_author)
#     # row['off_chain_start_date'] = key_info_elements[5].text
#     # row['off_chain_end_date'] = key_info_elements[6].text
#     # #Preliminary discussion
#     # row['prelim_sentiments'] = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
#     # prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
#     # # print(prem_other_details)
#     # elements = prem_other_details.split(" by ")
#     # element1 = elements[0]
#     # element2 = elements[1].split(" on ")[0]
#     # element3 = elements[1].split(" on ")[1]
#     # row['prelim_discussion_start_date'], row['prelim_author'], row['prelim_location'] = [element1, element2, element3]
#     # off_chain_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1) .jss25")[0]
#     # off_chain_option_list = [f"{element}%" for element in off_chain_votes.text.replace('Active Vote',"").replace("Cast Your Vote","").split("%")][:-1]
#     # option_dict = {}
    
# #     on_chain_author = key_info_elements[0].text.replace('Author',"")

# #     # print(summary)
# #     # on chain active
# #     # on-chain details
# #     on_chain_info_elements = soup.select(".css-1s50f5r+ .css-1s50f5r")[0]
# #     # print(on_chain_info_elements.text)
# #     on_chain_option_list = [f"{element}%" for element in on_chain_info_elements.text.replace('Active Vote',"").replace("Cast Your Vote","")\
# #         .replace('Results',"").split("%")][:-1]
# #     option_dict = {}
# #     for index, option in enumerate(on_chain_option_list, start=1):
# #         option_dict[f"on_chain_Option_{index}"] = option
# #     print(option_dict)
# #     print(on_chain_option_list)
    
# #     key_info_elements = soup.find_all('div', 'MuiBox-root css-z53l98')
# #     on_chain_author = key_info_elements[0].text.replace('Author',"")
# #     on_chain_end_date = soup.find('div', class_= "MuiContainer-root MuiContainer-maxWidthMd css-1u2mkel").find('div', class_ = "MuiBox-root css-1isemmb").text
# #     on_chain_start_date = soup.find_all('div', class_="MuiStep-root MuiStep-vertical css-0")[1].text.replace("ACTIVE VOTE","")
# #     print(on_chain_start_date)
# #     # row['temp_check_start_date'] = key_info_elements[5].text
# #     # row['temp_check_end_date'] = key_info_elements[6].text
    
# # #     temp_check_author = key_info_elements[0].text.replace('Author',"")
# # #     off_chain_start_date = key_info_elements[5].text
# # #     off_chain_end_date = key_info_elements[6].text
# # #     # print(off_chain_author,off_chain_start_date,off_chain_end_date)
    
# #     #Preliminary discussion
# #     prelim_sentiments = soup.find('div',id= "preliminary-discussion").find('div', class_="MuiBox-root css-70qvj9").text
# #     print(prelim_sentiments)
# #     prem_other_details = soup.find('div',id= "preliminary-discussion").find('div').find('div').text
# #     # print(prem_other_details)
# #     elements = prem_other_details.split(" by ")
# #     element1 = elements[0]
# #     element2 = elements[1].split(" on ")[0]
# #     element3 = elements[1].split(" on ")[1]
# #     prelim_bottom_date, prelim_author, prelim_location = [element1, element2, element3]
# #     print(prelim_bottom_date, prelim_author, prelim_location)
    
# #     temp_check_votes = soup.select(".css-178yklu .css-15j76c0:nth-child(1)")[0]
# #     temp_check_option_list = [f"{element}%" for element in temp_check_votes.text.replace('Active Vote',"").replace("Cast Your Vote","")\
# #         .replace('Results',"").split("%")][:-1]
# #     option_dict = {}
# #     for index, option in enumerate(temp_check_option_list, start=1):
# #         option_dict[f"temp_check_Option_{index}"] = option
# #     print(option_dict)
# #     print(temp_check_option_list)
    
    
    
#     # print(option_dict)
#     # # print(summary)