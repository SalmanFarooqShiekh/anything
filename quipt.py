from utilities import print_to_LL, print_to_PP, pdf_to_pages, empty_dir, display_alert, timestamp
from utilities import print_to_LL_stub, print_to_PP_stub
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import datetime
import time
import sys
import os

# Purpose of this script: It is meant to be run in the background and it will be watching a folder. 
# If anything pops up in that folder, it will be forwarded to the physical printer after processing it.
# The folder being watched is where the Quipt Virtual Printer will be saving the documents.

# Unless otherwise mentioned, VP refers to a "Virtual Printer" in this file

# Accompanying VP: https://github.com/rodyager/RWTS-PDFwriter

# Script Options:
QUIPT_VP_DESTINATION_FOLDER_PATH    = r"/private/var/spool/pdfwriter/apple"
SPLIT_QUIPT_PDF_TARGET              = r"./split_quipt_pdf_target/"

USE_LOG_FILE                        = True # if False, print log to the the stdout which is usually the terminal 
LOG_FILE_PATH                       = "./" + __file__ + ".log"

PRINT_TO_PHYSICAL_PRINTER           = False
WAIT_TIME_DUE_TO_VP_SAVING_THE_FILE = 10 # in seconds


###############################################################################################

if USE_LOG_FILE:
    sys.stdout = open(LOG_FILE_PATH, "at")

# Not so important:
ready_text = ": Ready to receive new quipt pdf's...\n"

class QuiptWatcher:
    def __init__(self):
        self.observer = Observer()

    def start(self):
        self.observer.schedule(QuiptPDFHandler(), QUIPT_VP_DESTINATION_FOLDER_PATH)
        self.observer.start()
        print(timestamp() + ready_text, flush=True)

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
            print(timestamp() + ": Done")
            self.observer.stop()
            self.observer.join()
        except:
            print(timestamp() + ": An error occured while running: " + __file__, flush=True)
            display_alert(r"An error occured while running: " + __file__, blocking=False)
            self.observer.stop()
            self.observer.join()


class QuiptPDFHandler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        # When _PDFwriter_ (https://github.com/rodyager/RWTS-PDFwriter) starts "printing" the pdf to the 
        # folder, this method is fired before PDFwriter completes writing the pdf. So we add some
        # delay to give (more than) enough time to PDFwriter to complete writing the pdf.
        time.sleep(WAIT_TIME_DUE_TO_VP_SAVING_THE_FILE)
        
        # From here on, you can (with very high probability) safely do whatever you want with the source pdf:
        path_to_source_pdf = event.src_path
        print(timestamp() + ": Quipt-PDF received at: '" + path_to_source_pdf + "'", flush=True)

        # create it if it doesn't exist already
        if not os.path.exists(SPLIT_QUIPT_PDF_TARGET):
            os.mkdir(SPLIT_QUIPT_PDF_TARGET)

        # delete the old contents of the split_quipt_pdf_target to keep its size from
        # growing indefinitely, old contents are not of use for anything at this point:
        empty_dir(SPLIT_QUIPT_PDF_TARGET)

        pages_paths = None
        # if any error occurs, proceed to deleting the source pdf
        try:
            # extract individual pages from the pdf
            pages_paths = pdf_to_pages(path_to_source_pdf, SPLIT_QUIPT_PDF_TARGET)
            print(timestamp() + ": File at '" + path_to_source_pdf + "' split successfuly to '" + SPLIT_QUIPT_PDF_TARGET + "'", flush=True)
        except Exception as e:
            error_msg =  timestamp() + ": " + __file__ + ": error while splitting the received pdf into individual pages."
            print(error_msg, flush=True)
            display_alert(error_msg, blocking=False)
            
        if pages_paths != None:
            # splitting was successful
            page_count = len(pages_paths)
            for page_no in range(1, page_count+1, 2):
                # processing one page-pair per iteration of the loop

                current_order_packing_slip_path = pages_paths[page_no]   # Odd Page/1
                current_order_pick_list_path    = pages_paths[page_no+1] # Even Page/2

                # the collation happens in this piece of code:
                if PRINT_TO_PHYSICAL_PRINTER:
                    print_to_LL(current_order_pick_list_path)    # Even Page/2 -> LL
                    print_to_PP(current_order_packing_slip_path) # Odd  Page/1 -> PP
                    print_to_PP(current_order_pick_list_path)    # Even Page/2 -> PP
                else:
                    print_to_LL_stub(current_order_pick_list_path)    # Even Page/2 -> LL
                    print_to_PP_stub(current_order_packing_slip_path) # Odd  Page/1 -> PP
                    print_to_PP_stub(current_order_pick_list_path)    # Even Page/2 -> PP


        # delete source pdf
        os.remove(path_to_source_pdf)
        print(timestamp() + ": Received PDF at path deleted: '" + path_to_source_pdf + "'", flush=True)
        print(timestamp() + ready_text, flush=True)

        
if __name__ == '__main__':
    print("\n\n" + timestamp() + ": " + __file__ + " started")
    w = QuiptWatcher()
    w.start()

