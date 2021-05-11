How to run async client ?
------------------------

Refer - https://confluence.cbsels.com/display/Electron/Generic+classifier+run+and+tests

Creation of input files: 
------------------------

Invoke create_input_files.py script. Below is an example for creation of input files where each files 
contains 1000 org strings and 50 such files:

$ python create_input_files.py

Enter number of org strings in file: 1000

Enter number of files to be created : 50

This will create files in input_files/50 directory where directory name 50 is picked based on input provided for "Enter number of files to be created" input 

 Execution of input files all sent out to GC asynchronously (no specification of number of threads):
------------------------------------------------------------------------------------------------
This will send out all requests concurrently using files created in input_files directory in previous step.
The logic to validate if input and output are as per expected values is not present and this was 
used to find out ideal batch size.

$ python client_asyncio.py

Enter files directory to be processed : input_files/50

Enter number of files to execute in that directory : 50
