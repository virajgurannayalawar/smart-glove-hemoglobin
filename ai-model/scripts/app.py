import streamlit as st
import subprocess
import os


st.title("AI Hemoglobin Detection System")

uploaded_file = st.file_uploader(
    "Upload a Nail Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:

    st.image(uploaded_file)

    st.success("Image Uploaded Successfully")

    if st.button("Predict Hemoglobin"):

        temp_path = "temp.jpg"

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        result = subprocess.check_output(
            ["python", "predict.py", temp_path],
            text=True
        )

        st.success(result)