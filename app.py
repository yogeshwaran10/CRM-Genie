from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import re
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_response():
    # Get user input from the request
    user_input = request.json.get('prompt', '')

    # Define the columns available in the database
    db_columns = [
        "customer_name", "customer_industry", "customer_region", 
        "customer_employee_size", "about_customer_overview", "tam_name", 
        "partner_info", "referenceable_or_not", "department_owning_abcompany", 
        "implementation_use_case", "competitor_previously_used", 
        "competitor_currently_using", "other_tools_used", 
        "use_cases_solved_with_abcompany", 
        "number_of_processes_apps_built_boards_integrations", 
        "integrations_with_abcompany", "case_study_if_available", 
        "industry_overview", "industry_specific_use_cases_abcompany_can_solve", 
        "roi_calculations_for_each"
    ]

    # Prompt for CodeLLama to generate SQL query
    prompt = f"""
    Generate a valid SQL SELECT query for the `customerinfo` table based on the user input. 
    Available columns: {', '.join(db_columns)}

    Rules:
    1. Use only SELECT operations
    2. Return query only
    3. Ensure query matches user intent: {user_input}
    4. Format response as valid JSON with 'SQL QUERY' key
    
    Example output:
    {{"SQL QUERY": "SELECT * FROM customerinfo WHERE customer_name LIKE '%example%'"}}
    """

    try:
        # Ollama API endpoint
        ollama_url = 'http://localhost:11434/api/generate'
        
        # Payload for Ollama API
        payload = {
            "model": "codellama:latest",
            "prompt": prompt,
            "stream": False
        }
        
        # Send request to Ollama
        response = requests.post(ollama_url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            # print(result)
            generated_text = result.get('response', '').strip()
            
            # Extract JSON from the response
            try:
                # Use regex to find JSON-like content
                json_match = re.search(r'\{.*?\}', generated_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_json = json.loads(json_str)
                    sql_query = parsed_json.get('SQL QUERY', '')
                else:
                    # Fallback: Try to extract query directly
                    sql_query = re.search(r'SELECT.*', generated_text, re.IGNORECASE | re.DOTALL)
                    sql_query = sql_query.group(0) if sql_query else ''
                    print(sql_query)
            except (json.JSONDecodeError, AttributeError):
                # Last resort: try to extract query manually
                sql_query = re.search(r'SELECT.*', generated_text, re.IGNORECASE | re.DOTALL)
                sql_query = sql_query.group(0) if sql_query else ''

            # Validate and clean the SQL query
            if sql_query and 'SELECT' in sql_query.upper():
                # Append semicolon if not present
                if not sql_query.rstrip().endswith(';'):
                    sql_query = sql_query.rstrip() + ';'
                
                # Connect to the SQLite database
                connection = sqlite3.connect("F:/IBM/customerdata.db")
                cursor = connection.cursor()
                
                try:
                    # Execute the generated SQL query
                    cursor.execute(sql_query)
                    
                    # Fetch all rows from the result
                    rows = cursor.fetchall()
                    
                    # Get column names
                    column_names = [description[0] for description in cursor.description]
                    
                    # Close the connection
                    connection.close()
                    
                    # If data is returned, send it to the user
                    return jsonify({
                        "success": True,
                        "query": sql_query,
                        "columns": column_names,
                        "data": rows
                    })
                
                except sqlite3.Error as e:
                    return jsonify({
                        "success": False,
                        "error": f"SQLite error: {str(e)}",
                        "query": sql_query
                    })
            
            else:
                return jsonify({
                    "success": False,
                    "error": "No valid SQL query generated."
                })
        
        else:
            return jsonify({
                "success": False,
                "error": f"Ollama API returned status code {response.status_code}"
            })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)