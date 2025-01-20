import os
import json
import csv

def json_to_csv(input_folder, output_csv):
    # List to hold all data from JSON files
    data_list = []

    # Get a list of all JSON files in the folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.json'):
            file_path = os.path.join(input_folder, file_name)
            
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    # Ensure the JSON is a dictionary or a list of dictionaries
                    if isinstance(data, dict):
                        data_list.append(data)
                    elif isinstance(data, list):
                        data_list.extend(data)
                    else:
                        print(f"Skipping {file_name}: Unsupported JSON structure")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {file_name}: {e}")

    # Write data to a CSV file
    if data_list:
        # Get the union of all keys in the data for the CSV header
        keys = set()
        for item in data_list:
            keys.update(item.keys())
        
        keys = sorted(keys)  # Sort keys for consistent column order

        with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data_list)

        print(f"CSV file saved to {output_csv}")
    else:
        print("No valid JSON data to write to CSV.")

# Specify the folder containing JSON files and the output CSV file
input_folder = "D:/Coachak RAG/free-exercise-db-main/free-exercise-db-main/exercises"
output_csv = "my_data.csv"

json_to_csv(input_folder, output_csv)
