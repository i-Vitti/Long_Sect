import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
import subprocess
import io
import base64
import re


# Initialize session state for data storage
if "data_table" not in st.session_state:
    st.session_state["data_table"] = pd.DataFrame()


# Helper functions for OCR and preprocessing
def preprocess_image(image):
    """
    Preprocess the image to enhance text recognition.
    """
    # Convert to grayscale
    gray_image = image.convert("L")
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2)
    
    return enhanced_image


def extract_text_with_llamaocr(image):
    """
    Use LlamaOCR (via Node.js script) to extract text from the image.
    """
    # Save preprocessed image to a temporary file
    temp_image_path = "temp_image.png"
    image.save(temp_image_path, format="PNG")

    # Run the Node.js script with subprocess
    try:
        result = subprocess.run(
            ["node", "llama_ocr.js", temp_image_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        st.error("Error running LlamaOCR: " + str(e))
        return ""


def parse_markdown_table(ocr_text):
    """
    Parse Markdown-style table text into a DataFrame, cleaning unnecessary rows and columns.
    """
    # Remove ** from text using regex
    cleaned_text = re.sub(r"\*\*(.*?)\*\*", r"\1", ocr_text)

    table_lines = cleaned_text.splitlines()
    table_data = []
    is_table = False

    for line in table_lines:
        # Detect and ignore separator lines (e.g., |---|---|---|---|)
        if "|" in line and "---" in line:
            is_table = True
            continue

        # Parse rows of the table
        if "|" in line:
            row = [cell.strip() for cell in line.split("|") if cell.strip()]
            table_data.append(row)

    # Format as DataFrame
    if table_data:
        headers = table_data[0]  # Use the first row as headers
        headers = [header.strip() for header in headers]  # Clean headers
        data = table_data[1:]  # Remaining rows are data

        # Pad rows to match the number of headers
        max_columns = len(headers)
        data = [row + [""] * (max_columns - len(row)) for row in data]

        # Ensure the table has the correct structure
        df = pd.DataFrame(data, columns=headers)

        # Remove unnecessary rows and columns
        df = df.loc[~df.iloc[:, 0].str.contains("EXISTING LEVELS", case=False, na=False)]  # Remove duplicate "EXISTING LEVELS" rows
        df = df.reset_index(drop=True)  # Reset index
        df.columns.name = None  # Remove index name

        # Convert numeric data where possible
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    else:
        return pd.DataFrame()


# Tab structure
tabs = st.tabs(["Home", "Upload & OCR", "Data Table", "Visualization", "Export", "Instructions"])

# 1. Home Tab
with tabs[0]:
    st.title("Pipeline Profile Survey Data App")
    st.markdown("""
    Welcome to the Pipeline Profile Survey Data App! This tool is designed for engineers to extract and consolidate 
    pipeline profile data from vintage drawings using OCR. Follow the steps in the tabs to process your images, 
    build a data table, and export the results as an Excel file.
    """)

# 2. Upload & OCR Tab
with tabs[1]:
    st.header("Upload Images for OCR")
    uploaded_files = st.file_uploader("Upload magnified pipeline profile images", accept_multiple_files=True, type=["png", "jpg", "jpeg", "tiff"])
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            st.write("Processing image with LlamaOCR...")
            
            # Perform OCR on the image
            preprocessed_image = preprocess_image(image)
            ocr_text = extract_text_with_llamaocr(preprocessed_image)
            st.write("Raw OCR Text Output:")
            st.text(ocr_text)
            
            # Parse OCR text into a table
            ocr_data = parse_markdown_table(ocr_text)
            if not ocr_data.empty:
                st.write("Extracted Data:")
                st.dataframe(ocr_data)
                # Append OCR data to the session state table
                st.session_state["data_table"] = ocr_data
            else:
                st.write("No valid data extracted. Please check the image quality or text format.")

# 3. Data Table Tab
with tabs[2]:
    st.header("Consolidated Data Table")
    if not st.session_state["data_table"].empty:
        st.dataframe(st.session_state["data_table"])
        st.markdown("You can review the data here. Any corrections should be made directly to the table before exporting.")
    else:
        st.write("No data available. Please upload images to extract data.")

# 4. Visualization Tab
with tabs[3]:
    st.header("Pipeline Profile Visualization")
    if not st.session_state["data_table"].empty:
        data = st.session_state["data_table"].copy()

        # Normalize column names for consistent access
        data.columns = [col.strip().upper() for col in data.columns]

        # Detect "CHAINAGE" or similar column for x-axis
        potential_x_axis = [col for col in data.columns if "CHAINAGE" in col]
        if not potential_x_axis:
            st.error("No column resembling 'CHAINAGE' found. Please check your data.")
        else:
            x_axis = potential_x_axis[0]  # Use the first match
            st.write(f"Using '{x_axis}' as the x-axis.")

            # Ensure numeric data for the x-axis and y-axis
            data[x_axis] = pd.to_numeric(data[x_axis], errors="coerce")
            numeric_columns = [col for col in data.columns if col != x_axis and "DEPTH TO INVERT" not in col]

            for col in numeric_columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")
            data = data.dropna(subset=[x_axis])  # Drop rows where x-axis values are missing

            # Plot data
            fig, ax = plt.subplots()
            for col in numeric_columns:
                ax.plot(data[x_axis], data[col], label=col, marker="o")
            ax.set_xlabel("Chainage")
            ax.set_ylabel("Values")
            ax.set_title("Pipeline Profile Visualization")
            ax.legend()
            st.pyplot(fig)
    else:
        st.write("No data available for visualization. Please upload images to extract data.")

# 5. Export Tab
with tabs[4]:
    st.header("Export Data and Visualization")
    if not st.session_state["data_table"].empty:
        # Export Table to Excel
        def export_to_excel():
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                st.session_state["data_table"].to_excel(writer, index=False, sheet_name="Pipeline Data")
            processed_data = output.getvalue()
            return processed_data

        excel_data = export_to_excel()
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="pipeline_data.xlsx">Download Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)

    else:
        st.write("No data available for export. Please upload images to extract data.")

# 6. Instructions Tab
with tabs[5]:
    st.header("Instructions")
    st.markdown("""
    **How to Use This App:**
    1. **Upload & OCR**: Upload magnified images of your vintage pipeline drawings for OCR processing.
    2. **Review Data**: Check the extracted data in the Data Table tab.
    3. **Visualize**: View the pipeline profile as a graph in the Visualization tab.
    4. **Export**: Download the consolidated data table and graph in the Export tab.
    """)
