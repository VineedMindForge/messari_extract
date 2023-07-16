import os
import pandas as pd

# Create an empty list to store individual DataFrames
dfs = []

# Specify the folder path containing the Excel files
folder_path = './proposal_extract/votes_extract/'

# Get a list of all the Excel files in the folder
file_list = [file for file in os.listdir(folder_path) if file.endswith('.xlsx')]

# Iterate through each file in the list
for file in file_list:
    # Construct the file path
    file_path = os.path.join(folder_path, file)
    
    # Read the Excel file into a DataFrame
    df = pd.read_excel(file_path)
    
    # Add a new column for the file name
    df['File Name'] = file.replace(".xlsx","")
    
    try:
        # Split the file name at underscores and assign the values to new columns
        df[['Coin', 'Index', 'Proposal_name', 'Stage']] = df['File Name'].str.split('_', expand=True)
    
    except:
        df[['Coin', 'Index', 'P1','P2', 'Stage']] = df['File Name'].str.split('_', expand=True)
        df['Proposal_name'] = df['P1'].str.cat(df['P2'], sep=' ')
        
    
    # Append the DataFrame to the list
    dfs.append(df)
    
    
# Append the DataFrame to the main DataFrame
appended_df = pd.concat(dfs, ignore_index=True)

appended_df = appended_df.drop(columns=['P1', 'P2'])

# Print the resulting DataFrame
print(appended_df.head())

appended_df.to_excel('./proposal_extract/all_votes.xlsx', sheet_name="consolidated", index=False)


