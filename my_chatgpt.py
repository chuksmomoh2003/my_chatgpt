#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import pandas as pd
import openai  # Make sure this is imported
import ast  # To check code safety and syntax
import re   # To extract and clean code blocks from the response
import matplotlib.pyplot as plt  # For plotting
import seaborn as sns  # For heatmap plotting
import plotly.express as px  # For interactive plotting

# Setting up Streamlit's UI
st.title("AI Data Assistant App")
st.write("This app answers questions about uploaded data and general topics. It also remembers past interactions.")

# Input field to request OpenAI API key from the user
openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
if openai_api_key:
    openai.api_key = openai_api_key  # Set the API key when provided

# Function to handle language model responses for generating code related to data analysis
def generate_code_for_query(df, question):
    columns_info = f"The dataset has columns: {', '.join(df.columns)}"
    prompt = (
        f"{columns_info}\nQuestion: {question}\n"
        "Generate Python code using pandas to answer this question. Use the DataFrame named 'df' directly. "
        "Do not import libraries or read external files. Store the result in a variable named 'result'. "
        "If a plot is needed, ensure it is displayed using Streamlit (st.pyplot() or st.plotly_chart())."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # Replace with your chosen model
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Function to clean and prepare code for execution
def clean_code(code):
    cleaned_code = re.sub(r'import\s+pandas\s+as\s+pd', '', code)
    cleaned_code = re.sub(r'pd\.', '', cleaned_code)
    cleaned_code = re.sub(r'#.*', '', cleaned_code)
    cleaned_code = cleaned_code.replace('to_datetime', 'pd.to_datetime')
    cleaned_code = cleaned_code.replace('plt.show()', 'st.pyplot(fig)')
    
    # Replace any standalone 'to_numeric' with 'pd.to_numeric'
    cleaned_code = cleaned_code.replace('to_numeric', 'pd.to_numeric')
    
    return cleaned_code.strip()

# Function to extract code from the response
def extract_code_from_response(response):
    code_match = re.search(r'```python(.*?)```', response, re.DOTALL)
    if code_match:
        return clean_code(code_match.group(1).strip())
    else:
        return clean_code(response.strip())

# Updated execute_code function
def execute_code(code, df):
    local_vars = {'df': df, 'pd': pd, 'plt': plt, 'sns': sns, 'px': px, 'st': st}  # Ensure 'pd' is included
    try:
        parsed_code = ast.parse(code)
        exec(code, {}, local_vars)
        if 'result' in local_vars:
            return local_vars['result']
        else:
            # Check if a plot was generated using Matplotlib
            if plt.get_fignums():
                fig, ax = plt.subplots()  # Create a figure and axes
                fig = plt.gcf()  # Get the current figure
                st.pyplot(fig)  # Pass the figure to st.pyplot()
                plt.clf()  # Clear the figure after displaying
                return "Plot displayed successfully."
            return "Code executed successfully, but no 'result' variable was found."
    except SyntaxError as se:
        return f"Syntax error in generated code: {se}"
    except Exception as e:
        return f"Error executing code: {e}"

# File upload section
uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if 'history' not in st.session_state:
    st.session_state['history'] = []

df = None  # Initialize df as None

# Processing uploaded files
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, low_memory=False)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.write("Data Preview:")
        st.dataframe(df)
        
        # Ask any question about the data
        question = st.text_input("Ask any question about the data:")
        if question and openai_api_key and df is not None:
            try:
                code_snippet = generate_code_for_query(df, question)
                st.write("Generated Code:")
                st.code(code_snippet)
                
                code_to_execute = extract_code_from_response(code_snippet)
                
                answer = execute_code(code_to_execute, df)
                st.session_state['history'].append({'question': question, 'answer': answer})
                
                if isinstance(answer, pd.DataFrame):
                    st.write("Answer:")
                    st.dataframe(answer)
                else:
                    st.write("Answer:", answer)
            except Exception as e:
                st.error(f"Error processing query: {e}")
        elif not openai_api_key:
            st.warning("Please enter your OpenAI API key to proceed.")
    except Exception as e:
        st.error(f"Error reading the file: {e}")

# General question input
general_question = st.text_input("Ask any general question:")
if general_question and openai_api_key:
    try:
        response = handle_general_question(general_question)
        st.session_state['history'].append({'question': general_question, 'answer': response})
        st.write("Answer:", response)
    except Exception as e:
        st.error(f"Error answering the question: {e}")
elif not openai_api_key and general_question:
    st.warning("Please enter your OpenAI API key to proceed.")

# Display interaction history
if st.session_state['history']:
    st.write("Interaction History:")
    for qa in st.session_state['history']:
        st.write(f"Q: {qa['question']}")
        st.write(f"A: {qa['answer']}")


# In[ ]:




