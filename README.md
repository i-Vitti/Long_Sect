# Long_Sect
A refined OCR that extracts data from longitudinal drawings and outputs a table of data for users to copy and paste elsewhere for use. This app is aiming to ease the manual process of data extraction particuarly from old "blue and brown print" drawings

Explanation of Each Dependency:
  streamlit: For building the interactive web application.
  pandas: For handling the data table and converting OCR results into structured data.
  Pillow: For image preprocessing (grayscale conversion, contrast enhancement).
  matplotlib: For plotting the pipeline profile visualization.
  openpyxl: For exporting the table to Excel format.
  base64: For encoding the exported Excel file for download.
  re: For cleaning and parsing text output from the OCR.
  node: Needed to run the LlamaOCR Node.js script.

Instructions to Create requirements.txt:
  Save the above content into a file named requirements.txt.
  Run the following command to install all dependencies:
    pip install -r requirements.txt

pipelineprofileapp.streamlit.app
