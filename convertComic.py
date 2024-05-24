import argparse
import os
import shutil
import zipfile
import rarfile
import py7zr
import tempfile
from PIL import Image
import math as Math
from concurrent.futures import ThreadPoolExecutor
import time

# Define the executor globally if the conversion tasks will be frequently called
executor = ThreadPoolExecutor(max_workers=4)

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively convert all files in the input directory')

    parser.add_argument('-i', '--input', action='store', help='Input file or directory')
    parser.add_argument('-o', '--output', action='store', help='Output file or directory')

    # options for converting comic book files to another format (cbz, cbr, cb7)
    parser.add_argument('--convert-extension', action='store', help='Set the output conversion extension type', default='cbz')

    # options for converting images in comic book files to another image type (png, jpg, webp, original)
    parser.add_argument('--convert-image-file-type', action='store', help='Set the image type used for the images in comic book files', default='webp')

    parser.add_argument('-c', '--compress', action='store_true', help='Compress the comic book files')
    parser.add_argument('--compress-rate', action='store', help='Set the image compression rate for compressing comic book files', default=90)

    parser.add_argument('--comicinfo', action='store_true', help='Add an empty comicinfo.xml file to hold comicbook metadata')

    args = parser.parse_args()

    return args

def validate_arguments(args):
    if args.input is None:
        print('Error: Input file or directory not set')
        return False

    if args.output is None:
        print('Error: Output file or directory not set')
        return False

    return True

def check_if_file_exists(file):
    return os.path.exists(file)

def check_if_directory_exists(directory):
    return os.path.isdir(directory)

def check_if_input_is_file_or_directory(input):
    
    if check_if_directory_exists(input):
        return 'directory'
    if check_if_file_exists(input):
        return 'file'
    else:
        return None
    
def check_if_file_is_comic_book_file(file):
    return file.lower().endswith(('.cbz', '.cbr', '.zip', '.rar', '.cb7', '.7z')) and not file[0] == '.'

def create_temp_directory(directory):
    temp_dir = tempfile.mkdtemp(dir=directory)
    return temp_dir

def determine_compression_type(file_path):
    signatures = {
        "ZIP": b"PK",
        "RAR": b"Rar!\x1A\x07\x00",
        "7Z": b"7z\xBC\xAF\x27\x1C"
    }

    with open(file_path, 'rb') as file:
        file_header = file.read(8)  # Read the first 8 bytes for checking

    for compression_type, signature in signatures.items():
        if file_header.startswith(signature):
            return compression_type

    return "Unknown"

'''
    decompresses a zip/cbz file into a directory, which is the output parameter
    file: the zip/cbz file to decompress
    output: the directory to decompress the file into

    returns True if the file was successfully uncompressed, False otherwise
'''
def decompress_zip_file(file, output):

    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(output)
        return True
    except Exception as e:
        print(f'Error: Failed to decompress ZIP file {file}')
        print(e)
        return False
    
'''
    decompress a rar/cbr file into a directory, which is the output parameter
    file: the rar/cbr file to decompress
    output: the directory to decompress the file into

    returns True if the file was successfully uncompressed, False otherwise
'''
def decompress_rar_file(file, output):
    try:
        with rarfile.RarFile(file, 'r') as rar_ref:
            rar_ref.extractall(output)
        return True
    except Exception as e:
        print(f'Error: Failed to decompress RAR file {file}')
        print(e)
        return False
    
'''
    decompress a 7z/cb7 file into a directory, which is the output parameter
    file: the 7z/cb7 file to decompress
    output: the directory to decompress the file into

    returns True if the file was successfully uncompressed, False otherwise
'''
def decompress_7z_file(file, output):
    try:
        with py7zr.SevenZipFile(file, mode='r') as archive:
            archive.extractall(output)
        return True
    except Exception as e:
        print(f'Error: Failed to decompress 7z file {file}')
        print(e)
        return False
    

'''
    converts an image file to a webp file, image file can be a .png, .jpg, .jpeg, .bmp, or .gif file
    imagePath: the path to the image file to convert

    returns True if the image was successfully converted and original file was deleted, False otherwise
'''
def convert_image_to_webp(image_path, compress_quality=100):
    try:
        # Open the image file
        with Image.open(image_path) as image:
            size_of_original = os.path.getsize(image_path)
            # resize the image to half its size
            if image.width > 3500 or image.height > 3500:
                image = image.resize((int(image.width/2), int(image.height/2)), Image.LANCZOS)

            # Convert the image to webp format
            webp_path = image_path.replace(image_path.split('.')[-1], 'webp')
            image = image.convert("RGB")  # Convert the image to RGB mode
            image.save(webp_path, 'webp', quality=compress_quality, optimize=True, lossless=False)

            size_of_webp = os.path.getsize(webp_path)
        
            # Delete the original image file if the webp file is smaller
            if size_of_webp < size_of_original:
                os.remove(image_path)
            else:
                os.remove(webp_path)
    except Exception as e:
        print(f'Error: Failed to convert webp image {image_path}')
        print(e)
        return False
    
'''
    converts an image file to a png file, image file can be a .jpg, .jpeg, .bmp, or .gif file
    imagePath: the path to the image file to convert

    returns True if the image was successfully converted, False otherwise
'''
def convert_image_to_png(image_path):
    try:
        # Open the image file
        with Image.open(image_path) as image:
            # Convert the image to png format
            png_path = image_path.replace(image.format.lower(), 'png')
            image.save(png_path, 'png')
        
        return True
    except Exception as e:
        print(f'Error: Failed to convert PNG image {image_path}')
        print(e)
        return False
    
'''
    converts an image file to a jpg file, image file can be a .png, .bmp, or .gif file
    imagePath: the path to the image file to convert

    returns True if the image was successfully converted, False otherwise
'''
def convert_image_to_jpg(image_path):
    try:
        # Open the image file
        with Image.open(image_path) as image:
            # Convert the image to RGB if it's not already in a compatible format
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')

            # Convert the image to jpg format
            jpg_path = image_path.replace(image_path.split('.')[-1], 'jpeg')
            image.save(jpg_path, 'jpeg', quality=1)
            
        os.remove(image_path)
        
        return True
    except Exception as e:
        print(f'Error: Failed to convert JPG image {image_path}')
        print(e)
        return False
    

def traverse_directory_for_image_webp_conversion(directory, compress, compress_rate):
    futures = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')) and not file[0] == '.':
                image_path = os.path.join(root, file)
                if compress:
                    #convertImageToWebp(image_path, compressRate)
                    future = executor.submit(convert_image_to_webp, image_path, compress_rate)
                    futures.append(future)
                else:
                    #convertImageToWebp(image_path)
                    future = executor.submit(convert_image_to_webp, image_path)
                    futures.append(future)

    for future in futures:
        future.result()

def traverse_directory_for_image_png_conversion(directory, compress, compress_rate):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                image_path = os.path.join(root, file)
                convert_image_to_png(image_path)

def traverse_directory_for_image_jpg_conversion(directory, compress, compress_rate):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.bmp', '.gif', '.webp')):
                image_path = os.path.join(root, file)
                convert_image_to_jpg(image_path)

'''
    compresses a directory into a cbz file

    directory: the directory to compress
    output: the directory to save the cbz file to
'''
def compress_directory_to_comic_book_file_cbz(directory, output):
    try:
        with zipfile.ZipFile(output, 'w') as zip_ref:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_ref.write(file_path, os.path.relpath(file_path, directory))
        return True
    except Exception as e:
        print(f'Error: Failed to compress directory {directory}')
        print(e)
        return False
    
'''
    compresses a directory into a cbr file

    directory: the directory to compress
    output: the directory to save the cbr file to
'''
def compress_directory_to_comic_book_file_cbr(directory, output):
    try:
        with rarfile.RarFile(output, 'w') as rar_ref:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    rar_ref.write(file_path, os.path.relpath(file_path, directory))
        return True
    except Exception as e:
        print(f'Error: Failed to compress directory {directory}')
        print(e)
        return False
    
'''
    compresses a directory into a cb7 file

    directory: the directory to compress
    output: the directory to save the cb7 file to
'''
def compress_directory_to_comic_book_file_cb7(directory, output):
    try:
        with py7zr.SevenZipFile(output, mode='w') as archive:
            archive.writeall(directory, directory)
        return True
    except Exception as e:
        print(f'Error: Failed to compress directory {directory}')
        print(e)
        return False
    
    
def delete_directory(directory):
    try:
        shutil.rmtree(directory)
        return True
    except Exception as e:
        print(f'Error: Failed to delete directory {directory}')
        print(e)
        return False
    
'''
    walks through a directory and returns a list of all the files in the directory, including subdirectories if recursive is set to True

    directory: the directory to walk through
    recursive: whether to walk through the directory recursively

    returns a list of all the files in the directory
'''
def parse_directory_for_files(directory, recursive):
    files = []
    for root, dirs, file_names in os.walk(directory):
        for file in file_names:
            if file[0] == '.':  # Skip hidden files
                continue
            files.append(os.path.join(root, file))
        if not recursive:
            break
    return files

'''
    walks through a directory and creates a copy of the directory structure in the directory passed in
'''
def copy_directory_structure(directory, output):
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            relative_path = os.path.relpath(dir_path, directory)
            output_dir = os.path.join(output, relative_path)
            os.makedirs(output_dir, exist_ok=True)
    
def output_directory_contents(directory):
    for root, dirs, files in os.walk(directory):
        print(f'Root: {root}')
        print(f'Directories: {dirs}')
        print(f'Files: {files}')
        print('')


def get_file_name_from_path(path):
    filename = os.path.basename(path)
    filename_without_extension = os.path.splitext(filename)[0]
    return filename_without_extension

def convert_comic_book(input, output, convert_extension, convert_image_file_type, compress, compress_rate, comicinfo, input_directory=None):
    temp_work_dir = create_temp_directory(output)

    file_compression_type = determine_compression_type(input)

    if file_compression_type == 'ZIP':
        decompress_zip_file(input, temp_work_dir)
    elif file_compression_type == 'RAR':
        status = decompress_rar_file(input, temp_work_dir)
    elif file_compression_type == '7Z':
        decompress_7z_file(input, temp_work_dir)
    else:
        print('Error: Unsupported compression type')
        return False
    
    #print(compress)
    #print(compressRate)
    #print(comicinfo)
    
    if convert_image_file_type == 'webp':
        #print('Converting images to webp')
        traverse_directory_for_image_webp_conversion(temp_work_dir, compress, compress_rate)
    elif convert_image_file_type == 'png':
        traverse_directory_for_image_png_conversion(temp_work_dir, compress, compress_rate)
    elif convert_image_file_type == 'jpg':
        traverse_directory_for_image_jpg_conversion(temp_work_dir, compress, compress_rate)
    elif convert_image_file_type == 'original':
        pass
    else:
        print('Error: Unsupported image conversion type')
        return False

    output_file_path = None

    if input_directory is not None:
        # remove the input directory from the input file path
        input_directory = os.path.abspath(input_directory)
        input_directory = input_directory + '/'
        input_path = input.replace(input_directory, '/')
        file_name = get_file_name_from_path(input_path)

        split_path = input_path.split('/')
        split_path.pop()  # remove the file name from the path
        input_path = '/'.join(split_path)
        # create the output file path

        output_file_path = output + input_path + '/' + file_name + '.' + convert_extension
        print('output ' + output_file_path)
    else:
        output_file_path = output + '/' + get_file_name_from_path(input) + '.' + convert_extension


    if output_file_path is None:
        print('Error: Output file path is not set')
        exit(1)

    if(convert_extension == 'cbz'):
        compress_directory_to_comic_book_file_cbz(temp_work_dir, output_file_path)
    elif(convert_extension == 'cbr'):
        compress_directory_to_comic_book_file_cbr(temp_work_dir, output_file_path)
    elif(convert_extension == 'cb7'):
        compress_directory_to_comic_book_file_cb7(temp_work_dir, output_file_path)
    else:
        print('Error: Unsupported conversion extension type')
        return False

    delete_directory(temp_work_dir)


if __name__ == '__main__':
    args = parse_arguments()
    if not validate_arguments(args):
        exit(1)

    input_type = check_if_input_is_file_or_directory(args.input)
    if input_type is None:
        print('Error: Input value is not valid')
        exit(1)

    output_valid = check_if_directory_exists(args.output)
    if not output_valid:
        print('Error: Output directory does not exist')
        exit(1)


    if input_type == 'file':
        if(check_if_file_is_comic_book_file(args.input)):
            convert_comic_book(args.input, args.output, args.convert_extension, args.convert_image_file_type, args.compress, args.compress_rate, args.comicinfo)
        else:
            print('Error: Input file is not a comic book file')

    start_time = time.time()
    if input_type == 'directory':
        files = parse_directory_for_files(args.input, args.recursive)

        copy_directory_structure(args.input, args.output)

        for file in files:
            if(check_if_file_is_comic_book_file(file)):
                print(f'Converting {file} - index {files.index(file) + 1} of {len(files)}')
                convert_comic_book(file, args.output, args.convert_extension, args.convert_image_file_type, args.compress, args.compress_rate, args.comicinfo, args.input)
    
    #print(f'Time taken: {time.time() - startTime}')
