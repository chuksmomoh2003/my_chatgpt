#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import pandas as pd
import openai
import ast  # To check code safety and syntax
import re   # To extract and clean code blocks from the response

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
        "Do not import libraries or read external files. Store the result in a variable named 'result'."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # Replace with your chosen model
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Function to handle general questions not related to data analysis
def handle_general_question(question):
    prompt = f"Question: {question}\nAnswer this question as best as you can."
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # Replace with your chosen model
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Function to clean and prepare code for execution
def clean_code(code):
    # Remove import statements and references to 'pd.'
    cleaned_code = re.sub(r'import\s+pandas\s+as\s+pd', '', code)
    cleaned_code = re.sub(r'pd\.', '', cleaned_code)
    cleaned_code = re.sub(r'#.*', '', cleaned_code)
    
    # Replace 'to_datetime' with direct pandas call via df (assume 'df' is available)
    cleaned_code = cleaned_code.replace('to_datetime', 'pd.to_datetime')
    
    return cleaned_code.strip()

# Function to extract code from the response
def extract_code_from_response(response):
    # Extract the code block between triple backticks
    code_match = re.search(r'```python(.*?)```', response, re.DOTALL)
    if code_match:
        return clean_code(code_match.group(1).strip())
    else:
        # Return the response directly if no code block is found, to attempt execution
        return clean_code(response.strip())

# Function to safely execute generated code
def execute_code(code, df):
    local_vars = {'df': df, 'pd': pd}  # Ensure 'pd' is in the local scope
    try:
        # Check code for valid syntax before execution
        parsed_code = ast.parse(code)
        
        # Execute the code only if syntax is valid
        exec(code, {}, local_vars)
        if 'result' in local_vars:
            return local_vars['result']
        else:
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
                
                # Extract only the code portion if necessary
                code_to_execute = extract_code_from_response(code_snippet)
                
                # Check the code snippet for basic formatting issues
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




