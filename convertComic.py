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

def parseArguments():
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

def validateArguments(args):
    if args.input is None:
        print('Error: Input file or directory not set')
        return False

    if args.output is None:
        print('Error: Output file or directory not set')
        return False

    return True

def checkIfFileExists(file):
    return os.path.exists(file)

def checkIfDirectoryExists(directory):
    return os.path.isdir(directory)

def checkIfInputIsFileOrDirectory(input):
    
    if checkIfDirectoryExists(input):
        return 'directory'
    if checkIfFileExists(input):
        return 'file'
    else:
        return None
    
def checkIfFileIsComicBookFile(file):
    return file.lower().endswith(('.cbz', '.cbr', '.zip', '.rar', '.cb7', '.7z')) and not file[0] == '.'

def createTempDirectory(directory):
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
def decompressZipFile(file, output):

    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(output)
        return True
    except Exception as e:
        print(f'Error: Failed to decompress file {file}')
        print(e)
        return False
    
'''
    decompress a rar/cbr file into a directory, which is the output parameter
    file: the rar/cbr file to decompress
    output: the directory to decompress the file into

    returns True if the file was successfully uncompressed, False otherwise
'''
def decompressRarFile(file, output):
    try:
        with rarfile.RarFile(file, 'r') as rar_ref:
            rar_ref.extractall(output)
        return True
    except Exception as e:
        print(f'Error: Failed to decompress file {file}')
        print(e)
        return False
    
'''
    decompress a 7z/cb7 file into a directory, which is the output parameter
    file: the 7z/cb7 file to decompress
    output: the directory to decompress the file into

    returns True if the file was successfully uncompressed, False otherwise
'''
def decompress7zFile(file, output):
    try:
        with py7zr.SevenZipFile(file, mode='r') as archive:
            archive.extractall(output)
        return True
    except Exception as e:
        print(f'Error: Failed to decompress file {file}')
        print(e)
        return False
    

'''
    converts an image file to a webp file, image file can be a .png, .jpg, .jpeg, .bmp, or .gif file
    imagePath: the path to the image file to convert

    returns True if the image was successfully converted and original file was deleted, False otherwise
'''
def convertImageToWebp(imagePath, compressQuality=100):
    try:
        # Open the image file
        with Image.open(imagePath) as image:
            sizeOfOriginal = os.path.getsize(imagePath)
            # resize the image to half its size
            if image.width > 3500 or image.height > 3500:
                image = image.resize((int(image.width/2), int(image.height/2)), Image.LANCZOS)

            # Convert the image to webp format
            webpPath = imagePath.replace(imagePath.split('.')[-1], 'webp')
            image = image.convert("RGB")  # Convert the image to RGB mode
            image.save(webpPath, 'webp', quality=compressQuality, optimize=True, lossless=False)

            sizeOfWebp = os.path.getsize(webpPath)
        
            # Delete the original image file if the webp file is smaller
            if sizeOfWebp < sizeOfOriginal:
                os.remove(imagePath)
            else:
                os.remove(webpPath)
    except Exception as e:
        print(f'Error: Failed to convert image {imagePath}')
        print(e)
        return False
    
'''
    converts an image file to a png file, image file can be a .jpg, .jpeg, .bmp, or .gif file
    imagePath: the path to the image file to convert

    returns True if the image was successfully converted, False otherwise
'''
def convertImageToPng(imagePath):
    try:
        # Open the image file
        with Image.open(imagePath) as image:
            # Convert the image to png format
            pngPath = imagePath.replace(image.format.lower(), 'png')
            image.save(pngPath, 'png')
        
        return True
    except Exception as e:
        print(f'Error: Failed to convert image {imagePath}')
        print(e)
        return False
    
'''
    converts an image file to a jpg file, image file can be a .png, .bmp, or .gif file
    imagePath: the path to the image file to convert

    returns True if the image was successfully converted, False otherwise
'''
def convertImageToJpg(imagePath):
    try:
        # Open the image file
        with Image.open(imagePath) as image:
            # Convert the image to RGB if it's not already in a compatible format
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')

            # Convert the image to jpg format
            jpgPath = imagePath.replace(imagePath.split('.')[-1], 'jpeg')
            image.save(jpgPath, 'jpeg', quality=1)
            
        os.remove(imagePath)
        
        return True
    except Exception as e:
        print(f'Error: Failed to convert image {imagePath}')
        print(e)
        return False
    

def traverseDirectoryForImageWebpConversion(directory, compress, compressRate):
    futures = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')) and not file[0] == '.':
                image_path = os.path.join(root, file)
                if compress:
                    #convertImageToWebp(image_path, compressRate)
                    future = executor.submit(convertImageToWebp, image_path, compressRate)
                    futures.append(future)
                else:
                    #convertImageToWebp(image_path)
                    future = executor.submit(convertImageToWebp, image_path)
                    futures.append(future)

    for future in futures:
        future.result()

def traverseDirectoryForImagePngConversion(directory, compress, compressRate):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                image_path = os.path.join(root, file)
                convertImageToPng(image_path)

def traverseDirectoryForImageJpgConversion(directory, compress, compressRate):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.bmp', '.gif', '.webp')):
                image_path = os.path.join(root, file)
                convertImageToJpg(image_path)

'''
    compresses a directory into a cbz file

    directory: the directory to compress
    output: the directory to save the cbz file to
'''
def compressDirectoryToComicBookFileCBZ(directory, output):
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
def compressDirectoryToComicBookFileCBR(directory, output):
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
def compressDirectoryToComicBookFileCB7(directory, output):
    try:
        with py7zr.SevenZipFile(output, mode='w') as archive:
            archive.writeall(directory, directory)
        return True
    except Exception as e:
        print(f'Error: Failed to compress directory {directory}')
        print(e)
        return False
    
    
def deleteDirectory(directory):
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
def parseDirectoryForFiles(directory, recursive):
    files = []
    for root, dirs, fileNames in os.walk(directory):
        for file in fileNames:
            if file[0] == '.':  # Skip hidden files
                continue
            files.append(os.path.join(root, file))
        if not recursive:
            break
    return files
    
def outputDirectoryContents(directory):
    for root, dirs, files in os.walk(directory):
        print(f'Root: {root}')
        print(f'Directories: {dirs}')
        print(f'Files: {files}')
        print('')


def getFileNameFromPath(path):
    filename = os.path.basename(path)
    filename_without_extension = os.path.splitext(filename)[0]
    return filename_without_extension

def convertComicBook(input, output, convertExtension, convertImageFileType, compress, compressRate, comicinfo):
    tempWorkDir = createTempDirectory(output)

    fileCompressionType = determine_compression_type(input)

    if fileCompressionType == 'ZIP':
        decompressZipFile(input, tempWorkDir)
    elif fileCompressionType == 'RAR':
        status = decompressRarFile(input, tempWorkDir)
    elif fileCompressionType == '7Z':
        decompress7zFile(input, tempWorkDir)
    else:
        print('Error: Unsupported compression type')
        return False
    
    #print(compress)
    #print(compressRate)
    #print(comicinfo)
    
    if convertImageFileType == 'webp':
        #print('Converting images to webp')
        traverseDirectoryForImageWebpConversion(tempWorkDir, compress, compressRate)
    elif convertImageFileType == 'png':
        traverseDirectoryForImagePngConversion(tempWorkDir, compress, compressRate)
    elif convertImageFileType == 'jpg':
        traverseDirectoryForImageJpgConversion(tempWorkDir, compress, compressRate)
    elif convertImageFileType == 'original':
        pass
    else:
        print('Error: Unsupported image conversion type')
        return False

    outputFilePath = output + '/' + getFileNameFromPath(input) + '.' + convertExtension
    if(convertExtension == 'cbz'):
        compressDirectoryToComicBookFileCBZ(tempWorkDir, outputFilePath)
    elif(convertExtension == 'cbr'):
        compressDirectoryToComicBookFileCBR(tempWorkDir, outputFilePath)
    elif(convertExtension == 'cb7'):
        compressDirectoryToComicBookFileCB7(tempWorkDir, outputFilePath)
    else:
        print('Error: Unsupported conversion extension type')
        return False

    deleteDirectory(tempWorkDir)


if __name__ == '__main__':
    args = parseArguments()
    if not validateArguments(args):
        exit(1)

    inputType = checkIfInputIsFileOrDirectory(args.input)
    if inputType is None:
        print('Error: Input value is not valid')
        #exit(1)

    outputValid = checkIfDirectoryExists(args.output)
    if not outputValid:
        print('Error: Output directory does not exist')
        exit(1)


    if inputType == 'file':
        if(checkIfFileIsComicBookFile(args.input)):
            convertComicBook(args.input, args.output, args.convert_extension, args.convert_image_file_type, args.compress, args.compress_rate, args.comicinfo)
        else:
            print('Error: Input file is not a comic book file')

    startTime = time.time()
    if inputType == 'directory':
        files = parseDirectoryForFiles(args.input, args.recursive)

        for file in files:
            if(checkIfFileIsComicBookFile(file)):
                print(f'Converting {file} - index {files.index(file) + 1} of {len(files)}')
                convertComicBook(file, args.output, args.convert_extension, args.convert_image_file_type, args.compress, args.compress_rate, args.comicinfo)
    
    #print(f'Time taken: {time.time() - startTime}')
        
