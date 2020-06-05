import os
import glob
import time
import datetime
from PyPDF2 import PdfFileWriter, PdfFileReader

physical_printer_name = r"Ecomm_Fulfillment___Inventory_Cage" # as determined from running 'lpstat -a' in the terminal

# PP means Plain Paper, the print media in Tray1 of the printer
def print_to_PP(path_to_file_to_print):
    os.system(r"lpr -P " + physical_printer_name + " -o BRInputSlot=Tray1 " + path_to_file_to_print)
    print("Sending print job to PP/Tray1 done: " + path_to_file_to_print, flush=True)


# LL means Laser Labels, the print media in Tray2 of the printer
def print_to_LL(path_to_file_to_print):
    os.system(r"lpr -P " + physical_printer_name + " -o BRInputSlot=Tray2 " + path_to_file_to_print)
    print("Sending print job to LL/Tray2 done: " + path_to_file_to_print, flush=True)


def print_to_PP_stub(path_to_file_to_print):
    print("Sending print job to PP/Tray1 done: " + path_to_file_to_print, flush=True)


def print_to_LL_stub(path_to_file_to_print):
    print("Sending print job to LL/Tray2 done: " + path_to_file_to_print, flush=True)


# Breaks the pdf at path_to_pdf into individual pdf's each of which contains one page of 
# the source pdf, saving each one-page-pdf to output_dir. 
#
# Returns a dict of size=(number of pages in path_to_pdf) which contains the path to each
# one-page-pdf. The keys are integers and values are path strings in the dict. The paths 
# in the dict are relative to .
# 
# Example Usage: 
# pages_of_pdf = pdf_to_pages(r"path/to/your.pdf")
# page1_path   = pages_of_pdf[1]  # note that indexing of the dict starts from 1 to
# page2_path   = pages_of_pdf[2]  # match with indexing of page numbers of the pdf,
# page3_path   = pages_of_pdf[3]  # this was the reason a dict was used instead of a list
# ...and so on
def pdf_to_pages(path_to_pdf, output_dir):
    # ensure '/' at the end of output_dir path string:
    output_dir = output_dir + ("" if output_dir[-1] == "/" else "/")

    if not os.path.exists(output_dir):
        raise NotADirectoryError(output_dir)

    # will be populated and returned:
    paths = dict() 

    # split the pdf:
    with open(path_to_pdf, "rb") as opened_pdf:
        reader = PdfFileReader(opened_pdf)

        for i in range(reader.numPages):
            writer = PdfFileWriter()
            writer.addPage(reader.getPage(i))

            output_page_path = f"{output_dir}page_{i+1:04}.pdf"
            with open(output_page_path, "wb") as output_stream:
                writer.write(output_stream)
            
            paths[i+1] = output_page_path

    return paths


# deletes all contents of the given directory
def empty_dir(dir_path):
    dir_path = dir_path + ("" if dir_path[-1] == "/" else "/")
    files = glob.glob(dir_path + "*")
    for file in files:
        os.remove(file)


# it will be a little better if this is passed rstrings
def display_alert(msg, blocking):
    os.system(r'osascript -e "display alert \"' + msg + r'\""' + ('' if blocking else ' &'))


# returns a timestamp of the current local time as a string
def timestamp():
    return datetime.datetime.now().strftime("%d.%b %Y, %H:%M:%S")

#######################################################################################################################

# for testing:

def print_to_Quipt(path_to_file_to_print):
    os.system(r"lpr -P Quipt " + path_to_file_to_print)

def print_to_Amazon(path_to_file_to_print):
    os.system(r"lpr -P Amazon " + path_to_file_to_print)


######################################################################################################################


if __name__ == "__main__":
    test_pdf = r"blahblahblah"

    ans = input("> Do you want to print 2 test pages? (p=to pyhsical printer/v=to virtual printer/n=do nothing): ")
    if ans == "p":
        print_to_LL(test_pdf)
        print_to_PP(test_pdf)
    elif ans == "v":
        print_to_Amazon(test_pdf)
        print_to_Quipt(test_pdf)
    else:
        print("Doing nothing... ", end="", flush=True)
        print("Done.", flush=True) # hehe
