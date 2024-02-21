from modules.utils import *

logger = configure_logging(streaming=True)
batchfiles = [file for file in os.listdir('ignore') if file.startswith('BATCH')]
batchfiles = ['ignore/' + filename for filename in batchfiles]
file_directory = sorted([file for file in os.listdir('ignore') if file.startswith('MAIN')])
if len(file_directory)>0:
    mainfile = file_directory[-1] # Gets latest file
    mainfilepath = f'ignore/{mainfile}'
main_df = update_main(mainfilepath, batchfiles)
main_df.to_excel(f"ignore/MAIN_{datetime.now().strftime('%Y-%m-%d')}.xlsx", engine='xlsxwriter')