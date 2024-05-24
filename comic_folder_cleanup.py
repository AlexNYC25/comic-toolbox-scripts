import os
import shutil
import sys

def organize_folders(base_folder_path):
    # Check if the given path is a directory
    if not os.path.isdir(base_folder_path):
        print(f"The provided path '{base_folder_path}' is not a valid directory.")
        return

    # Iterate through each folder in the base folder
    for folder_name in os.listdir(base_folder_path):
        if folder_name.startswith('.'):
            continue
        folder_path = os.path.join(base_folder_path, folder_name)
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_path}")
            organize_single_folder(folder_path)

def organize_single_folder(folder_path):
    # Define the path to the 'Single Issues' folder
    single_issues_folder = os.path.join(folder_path, "Single Issues")

    # Create the 'Single Issues' folder if it does not exist
    if not os.path.exists(single_issues_folder):
        os.makedirs(single_issues_folder)
        print(f"Created folder: {single_issues_folder}")

    # Move all contents of the folder into the 'Single Issues' folder
    for item in os.listdir(folder_path):
        if item.startswith('.'):
            continue
        item_path = os.path.join(folder_path, item)
        if item != "Single Issues":
            shutil.move(item_path, os.path.join(single_issues_folder, item))
            print(f"Moved {item} to {single_issues_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <base_folder_path>")
    else:
        base_folder_path = sys.argv[1]
        organize_folders(base_folder_path)
