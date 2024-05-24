import os
import sys
import zipfile
import xml.etree.ElementTree as ET

def list_files_in_folder(folder_path, year):
    # Check if the given path is a directory
    if not os.path.isdir(folder_path):
        print(f"The provided path '{folder_path}' is not a valid directory.")
        return

    # Print the provided year
    print(f"Year: {year}")

    # List all files in the given folder that don't start with '.' and end with '.cbz'
    print("Filtered files in the folder:")
    for filename in os.listdir(folder_path):
        if filename.startswith('.'):
            continue
        if filename.endswith('.cbz'):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                print(f"Processing file: {filename}")
                process_cbz_file(file_path, year)

def process_cbz_file(file_path, year):
    # Check if the file is a valid zip file
    if not zipfile.is_zipfile(file_path):
        print(f"File '{file_path}' is not a valid zip file.")
        return

    # Uncompress the file to a temporary directory
    temp_dir = os.path.join(os.path.dirname(file_path), "temp_unzip")
    os.makedirs(temp_dir, exist_ok=True)
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Check if 'ComicInfo.xml' exists in the uncompressed files
    comic_info_path = os.path.join(temp_dir, 'ComicInfo.xml')
    if os.path.isfile(comic_info_path):
        print(f"'ComicInfo.xml' found in '{file_path}'")
        # Modify the 'volume' property in 'ComicInfo.xml'
        modify_comic_info(comic_info_path, year)

    # Recompress the folder into the same original file name
    with zipfile.ZipFile(file_path, 'w') as zip_ref:
        for folder_name, subfolders, filenames in os.walk(temp_dir):
            for filename in filenames:
                file_path_in_zip = os.path.join(folder_name, filename)
                arcname = os.path.relpath(file_path_in_zip, temp_dir)
                zip_ref.write(file_path_in_zip, arcname)

    # Clean up the temporary directory
    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(temp_dir)

def modify_comic_info(file_path, year):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find the 'volume' element and set its text to the year
    volume_element = root.find('Volume')
    if volume_element is None:
        # Create a new 'volume' element if it doesn't exist
        volume_element = ET.SubElement(root, 'Volume')
    
    volume_element.text = str(year)

    # Save the modified XML back to the file
    tree.write(file_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <folder_path> <year>")
    else:
        folder_path = sys.argv[1]
        try:
            year = int(sys.argv[2])
            list_files_in_folder(folder_path, year)
        except ValueError:
            print("The year parameter should be a numeric value.")
