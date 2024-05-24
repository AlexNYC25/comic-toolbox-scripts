import os
import zipfile
import sys

def compress_folders_to_cbz(base_folder_path):
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
            cbz_file_path = os.path.join(base_folder_path, f"{folder_name}.cbz")
            print(f"Compressing folder: {folder_path} to {cbz_file_path}")
            compress_folder_to_cbz(folder_path, cbz_file_path)

def compress_folder_to_cbz(folder_path, cbz_file_path):
    with zipfile.ZipFile(cbz_file_path, 'w') as cbz_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                cbz_file.write(file_path, arcname)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <base_folder_path>")
    else:
        base_folder_path = sys.argv[1]
        compress_folders_to_cbz(base_folder_path)
