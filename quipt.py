from utilities import print_to_LL, print_to_PP, pdf_to_pages, empty_dir, display_alert, timestamp
from utilities import print_to_LL_stub, print_to_PP_stub
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from subprocess import Popen, PIPE
import datetime
import time
import sys
import os

display_alert("quipt started", blocking=False)

# Purpose of this script: It is meant to be run in the background and it will be watching a folder. 
# If anything pops up in that folder, it will be forwarded to the physical printer after processing it.
# The folder being watched is where the Quipt Virtual Printer will be saving the documents.

# Unless otherwise mentioned, VP refers to a "Virtual Printer" in this file

# Accompanying VP: Paid version of 'PDF Printer' from the Mac App Store

# Script Options:
PRINT_TO_PHYSICAL_PRINTER           = False
USE_LOG_FILE                        = False # if False, print log to the the stdout which is the terminal usually
QUIPT_VP_DESTINATION_FOLDER_PATH    = r"./quipt_virtual_printer_target"
SPLIT_QUIPT_PDF_TARGET              = r"./split_quipt_pdf_target/"
LOG_FILE_PATH                       = "./" + __file__ + ".log"
WAIT_TIME_DUE_TO_VP_SAVING_THE_FILE = 1 # in seconds


###############################################################################################

if USE_LOG_FILE:
    sys.stdout = open(LOG_FILE_PATH, "at")


ready_text = ": Ready to receive new quipt pdf's...\n" # Not so important:
class QuiptWatcher:
    def __init__(self):
        self.observer = Observer()

    def start(self):
        # create it if it doesn't exist already
        if not os.path.exists(QUIPT_VP_DESTINATION_FOLDER_PATH):
            os.mkdir(QUIPT_VP_DESTINATION_FOLDER_PATH)
            msg = "Set the folder where the quipt_system's Virtual Printer is saving the PDFs to: '" + QUIPT_VP_DESTINATION_FOLDER_PATH + "'"
            display_alert(msg, blocking=True)
        
        self.observer.schedule(QuiptPDFHandler(), QUIPT_VP_DESTINATION_FOLDER_PATH)
        self.observer.start()
        print("\n" + timestamp() + ready_text, flush=True)

        # The observer will keep observing in its own thread.
        # We are artificially keepthing this main thread alive 
        # because if it finishes execution, python will kill all 
        # its child threads too, which includes the observer's thread.
        # We just want this main thread to be alive through any means.
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            print(timestamp() + ": Closing all threads, please wait...", flush=True)
            self.observer.stop()
            self.observer.join()
            print(timestamp() + ": Done")
        except:
            print(timestamp() + ": An error occured while running: " + __file__, flush=True)
            display_alert(r"An error occured while running: " + __file__, blocking=False)
            self.observer.stop()
            self.observer.join()


class QuiptPDFHandler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        path_to_source_pdf = event.src_path

        # When 'PDF Printer' starts "printing" the pdf to the 
        # folder, this method is fired before 'PDF Printer' completes writing the pdf. So we add some
        # delay to give (more than) enough time to 'PDF Printer' to complete writing the pdf.
        print(timestamp() + ": Started receiving Quipt-PDF at: '" + path_to_source_pdf + "'", flush=True)
        print(timestamp() + ": Waiting for " + str(WAIT_TIME_DUE_TO_VP_SAVING_THE_FILE) + " seconds to complete the reception...", flush=True)
        time.sleep(WAIT_TIME_DUE_TO_VP_SAVING_THE_FILE)
        
        # From here on, you can (with very high probability) safely do whatever you want with the source pdf:
        print(timestamp() + ": Done waiting. Splitting Quipt-PDF received at: '" + path_to_source_pdf + "'", flush=True)

        # create it if it doesn't exist already
        if not os.path.exists(SPLIT_QUIPT_PDF_TARGET):
            os.mkdir(SPLIT_QUIPT_PDF_TARGET)

        # delete the old contents of the split_quipt_pdf_target to keep its size from
        # growing indefinitely, old contents are not of use for anything at this point:
        try:
            empty_dir(SPLIT_QUIPT_PDF_TARGET)
            print(timestamp() + ": Deleting all contents of dir at: '" + SPLIT_QUIPT_PDF_TARGET + "'", flush=True)
        except Exception as expp:
            error_msg =  timestamp() + ": " + __file__ + ": error while deleting deleting all contents of dir at: '" + SPLIT_QUIPT_PDF_TARGET + "'"
            print(error_msg, flush=True)


        pages_paths = None
        try:
            # extract individual pages from the pdf
            pages_paths = pdf_to_pages(path_to_source_pdf, SPLIT_QUIPT_PDF_TARGET)
            print(timestamp() + ": File at '" + path_to_source_pdf + "' split successfuly to '" + SPLIT_QUIPT_PDF_TARGET + "'", flush=True)
        except Exception as e:
            # if any error occurs, proceed to deleting the source pdf
            error_msg =  timestamp() + ": " + __file__ + ": error while splitting the received pdf into individual pages."
            print(error_msg, flush=True)
            # display_alert(error_msg, blocking=False)
            
        if pages_paths != None:
            # splitting was successful
            page_count = len(pages_paths)
            # quipt-pdfs have even number of pages, if a pdf with odd number of pages is received, do nothing with it
            if page_count % 2 == 0: 
                for page_no in range(1, page_count+1, 2):
                    # processing one page-pair per iteration of the loop
                    
                    current_order_packing_slip_path = pages_paths[page_no]   # Odd Page/1n
                    current_order_pick_list_path    = pages_paths[page_no+1] # Even Page/2n

                    # the collation happens in this piece of code:
                    if PRINT_TO_PHYSICAL_PRINTER:
                        print_to_LL(current_order_pick_list_path)            # Even Page/2n -> LL
                        print_to_PP(current_order_packing_slip_path)         # Odd  Page/1n -> PP
                        print_to_PP(current_order_pick_list_path)            # Even Page/2n -> PP
                    else:
                        print_to_LL_stub(current_order_pick_list_path)       # Even Page/2n -> LL
                        print_to_PP_stub(current_order_packing_slip_path)    # Odd  Page/1n -> PP
                        print_to_PP_stub(current_order_pick_list_path)       # Even Page/2n -> PP


        # delete source pdf
        try:
            os.remove(path_to_source_pdf)
            print(timestamp() + ": Received PDF at path deleted: '" + path_to_source_pdf + "'", flush=True)
        except Exception as exp:
            error_msg =  timestamp() + ": " + __file__ + ": error while deleting source pdf at: '" + path_to_source_pdf + "'"
            print(error_msg, flush=True)
            # display_alert(error_msg, blocking=False)

        print("\n" + timestamp() + ready_text, flush=True)

        # Close the Preview window opened by the 'PDF Printer'
        script = r'tell application "System Events" to click first button of (first window of process "Preview")'
        p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = p.communicate(script)

        
if __name__ == '__main__':
    print("\n\n" + timestamp() + ": " + __file__ + " started")
    w = QuiptWatcher()
    w.start()
