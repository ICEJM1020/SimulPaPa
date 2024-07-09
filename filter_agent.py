""" 
Description: 
Author: Jiachen Li
Date: 2024-06-19
""" 
import os
import json
import pandas as pd
import numpy as np
from scipy.stats import norm
import shutil
from config import CONFIG
diseases = ['Use assisted device', 'uncontrolled heart', 'stroke', 'high blood pressure', 'diabetes', 'osteoporosis', 'take more than four medications']
# Define the base directory containing the folders
print(CONFIG["base_dir"])
base_directory = CONFIG["base_dir"]+'/.Users/final_intervention_100/agents'

# Initialize an empty list to store the data
data_list = []

def select_rows_with_distribution(df, target_distribution, num_rows, max_iterations=10000):
    best_selection = None
    best_fitness = np.inf
    fitness = 0
    # Iterate to find the best selection of rows
    for _ in range(max_iterations):
        # Randomly select num_rows from df
        selected_rows = df.sample(n=num_rows, replace=False)
        
        # Calculate mean and std for each column
        means = selected_rows.mean()
        stds = selected_rows.std()
        fitness = 0
        # Calculate fitness (distance) from target_distribution
        for col in df.columns:
            fitness = fitness + (abs(means[col] - target_distribution[col]['mean']) +(abs(stds[col] - target_distribution[col]['std']) if 'std' in target_distribution[col] else 0)/3)*target_distribution[col]['weight']
        
        # for col in df.columns:
        #     if target_distribution[col]['type'] == 'category':
        #         if means[col]!=target_distribution[col]['mean']:
        #             fitness = np.inf
        #             break
        #     fitness = fitness + (abs(means[col] - target_distribution[col]['mean']) +(abs(stds[col] - target_distribution[col]['std']) if 'std' in target_distribution[col] else 0))/target_distribution[col]['mean']
        
        # Update best selection if current selection is better
        if fitness < best_fitness:
            best_fitness = fitness
            best_selection = selected_rows.copy()
    # Print mean and standard deviation in a readable format
    for column in best_selection.columns:
        print(f"Column: {column}")
        print(f"Mean: {best_selection.mean()[column]:.2f}, {num_rows*best_selection.mean()[column]:.2f}")
        print(f"Standard Deviation: {best_selection.std()[column]:.2f}")
        print("-" + "-" * len(column))
    print(best_selection)
    return best_selection

def save_dataframe(df, base_filename,directory,folder_list):
    # Initialize the counter
    counter = 0
    filename = f"{base_filename}.csv"
    
    # Check if the file already exists
    while os.path.isfile(os.path.join(directory,filename)):
        counter += 1
        filename = f"{base_filename}_{counter}.csv"
    
    # Save the DataFrame to the file
    df.to_csv(os.path.join(directory,filename), index=False)
    print(f"File saved as {filename}")

    target_directory = os.path.join(directory,filename.split('.')[0])
    # Create the target directory if it doesn't exist
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    # Loop through each number in the list and copy the corresponding folder
    for folder in folder_list:
        folder_name = str(folder)  # Convert number to string to use in file paths
        source_folder = os.path.join(directory, folder_name)
        target_folder = os.path.join(target_directory, folder_name)

        # Check if the source folder exists before copying
        if os.path.exists(source_folder):
            shutil.copytree(source_folder, target_folder)
            print(f"Folder {folder_name} copied to {target_directory}.")
        else:
            print(f"Folder {folder_name} does not exist in the source directory.")



# Iterate through each folder in the base directory
for folder_name in os.listdir(base_directory):
    folder_path = os.path.join(base_directory, folder_name)
    if os.path.isdir(folder_path):
        json_file_path = os.path.join(folder_path, 'info.json')
        if os.path.isfile(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data_dict = json.load(json_file)
                data_dict['agent_num'] = int(folder_name)  # Add folder name to the dictionary
                data_list.append(data_dict)

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(data_list)

# Set the folder name as the index
df.set_index('agent_num', inplace=True)
df = df.sort_values(by='agent_num')
# Change some data format
for disease in diseases:
    df[disease.replace(' ', '_').lower()] = df['disease'].apply(lambda x: 1 if disease.lower() in x.lower() else 0)
df['female'] = df['gender'].apply(lambda x: 1 if "female" in x.lower() else 0)
df['weight'] = df['weight'].apply(lambda x: float(x.split()[0]))
df['BMI'] = df['BMI'].apply(lambda x: float(x))
# # Save the DataFrame to a CSV file
# csv_file_path = 'all_info.csv'
# df.to_csv(csv_file_path)
# print(f"DataFrame saved to {csv_file_path}")


# Target mean and standard deviation for each column
target_control_distribution = {
    'female': {'mean': 8, 'std': 80, 'weight':1/4},
    'age': {'mean': 70.55, 'std': 7.5, 'weight':1/80},
    'BMI': {'mean': 30.15, 'std': 7.0, 'weight':1/30},
    'weight': {'mean': 179.95, 'std': 42.2, 'weight':1/180},
    'use_assisted_device': {'mean': 0.6, 'weight':1},
    'uncontrolled_heart': {'mean': 0.4, 'weight':1},
    'stroke': {'mean': 0.1, 'weight':1},
    'high_blood_pressure': {'mean': 0.6, 'weight':1},
    'diabetes': {'mean': 0.3, 'weight':1},
    'osteoporosis': {'mean': 0.6, 'weight':1},
    'take_more_than_four_medications': {'mean': 0.3, 'weight':1}
}

target_intervention_distribution = {
    'female': {'mean': 21, 'std': 80.8, 'weight':15/26},
    'age': {'mean': 69.31, 'std': 7.3, 'weight':1/70},
    'BMI': {'mean': 31.4, 'std': 7.4, 'weight':1/30},
    'weight': {'mean': 183.11, 'std': 39.8, 'weight':1/180},
    'use_assisted_device': {'mean': 8/26, 'weight':10/26},
    'uncontrolled_heart': {'mean': 7/26, 'weight':10/26},
    'stroke': {'mean': 6/26, 'weight':10/26},
    'high_blood_pressure': {'mean': 20/26, 'weight':10/26},
    'diabetes': {'mean': 11/26, 'weight':10/26},
    'osteoporosis': {'mean': 14/26, 'weight':10/26},
    'take_more_than_four_medications': {'mean': 12/26, 'weight':10/26}
}
#-----------------------------
# control
#columns_to_consider = list(target_control_distribution.keys())
#-----------------------------
#intervention
columns_to_consider = list(target_intervention_distribution.keys())

print(df.head(5))
df_subset = df[columns_to_consider]

#-----------------------------
# control
# Call the function to get selected rows
# selected_rows_num = select_rows_with_distribution(df_subset, target_control_distribution, 10).index.values.tolist()
# print(selected_rows_num)
# control_10 = df.loc[selected_rows_num]
# print(control_10)
# save_dataframe(control_10, "control_10",base_directory,selected_rows_num)
#-----------------------------


#------------------------------
# intervention
# Call the function to get selected rows
selected_rows_num = select_rows_with_distribution(df_subset, target_intervention_distribution, 26).index.values.tolist()
print(selected_rows_num)
intervention_26 = df.loc[selected_rows_num]
print(intervention_26)
save_dataframe(intervention_26, "intervention_26",base_directory,selected_rows_num)
#-----------------------------


# # # Save the DataFrame to a CSV file
# # csv_file_path = os.path.join(base_directory, 'control_10.csv')
# # control_10.to_csv(csv_file_path)
# # print(f"DataFrame saved to {csv_file_path}")
# # Save the DataFrame to a CSV file
# csv_file_path = os.path.join(base_directory, 'control_10.csv')
# control_10.to_csv(csv_file_path)
# print(f"DataFrame saved to {csv_file_path}")
