from flask import Flask, render_template, request, jsonify
import requests
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_response():
    # Get user input from the request
    user_input = request.json.get('prompt', '')

    # Define the columns available in the database with user-friendly names
    db_columns = [
        "Customer name", "Customer Industry", "Customer Region", "Customer employee size", 
        "About the customer (overview)", "TAM name", "Partner info", "Referenceable or not", 
        "Department implementing/owning abcompany", "Implementation use case", 
        "Competitor previously used", "Competitor currently using", "Other tools used", 
        "Use cases solved with abcompany", "Number of processes, apps built, boards, integrations", 
        "What are the integrations with abcompany", "Case study if available", "Industry Overview", 
        "Industry-specific use cases abcompany can solve", "ROI calculations for each"
    ]
    
    # Mapping the user-friendly column names to the actual database column names
    column_mapping = {
        "Customer name": "customer_name",
        "Customer Industry": "customer_industry",
        "Customer Region": "customer_region",
        "Customer employee size": "customer_employee_size",
        "About the customer (overview)": "about_customer_overview",
        "TAM name": "tam_name",
        "Partner info": "partner_info",
        "Referenceable or not": "referenceable_or_not",
        "Department implementing/owning abcompany": "department_owning_abcompany",
        "Implementation use case": "implementation_use_case",
        "Competitor previously used": "competitor_previously_used",
        "Competitor currently using": "competitor_currently_using",
        "Other tools used": "other_tools_used",
        "Use cases solved with abcompany": "use_cases_solved_with_abcompany",
        "Number of processes, apps built, boards, integrations": "number_of_processes_apps_built_boards_integrations",
        "What are the integrations with abcompany": "integrations_with_abcompany",
        "Case study if available": "case_study_if_available",
        "Industry Overview": "industry_overview",
        "Industry-specific use cases abcompany can solve": "industry_specific_use_cases_abcompany_can_solve",
        "ROI calculations for each": "roi_calculations_for_each"
    }

    # Create a prompt that includes both the user input and the available columns
    prompt = f"""
    You are a SQL query generator. The task is to generate a SQL query that reads data from the database 
    without making any modifications (no INSERT, UPDATE, or DELETE operations). 

    The available columns in the database are:
    {', '.join(db_columns)}

    The table name is `customerinfo`.

    Based on the following user input, generate a **valid SQL query only** that reads data from the `customerinfo` table, ensuring that no records are modified. 

    Do **not** include any additional explanations or context, only provide the SQL query.

    User input: "{user_input}"
    """

    try:
        # Ollama API endpoint for local model interaction
        ollama_url = 'http://localhost:11434/api/generate'
        
        # Payload for Ollama API
        payload = {
            "model": "codellama:latest",
            "prompt": prompt,
            "stream": False  # Set to False to get full response at once
        }
        
        # Send request to Ollama
        response = requests.post(ollama_url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            sql_query = result.get('response', '')
            
            # Print the generated SQL query for debugging purposes
            print("Generated SQL Query:", sql_query)
            
            # Now, map user-friendly column names to actual column names
            for user_friendly, db_column in column_mapping.items():
                sql_query = sql_query.replace(user_friendly, f'"{db_column}"')

            # Print the modified SQL query for debugging purposes
            print("Modified SQL Query:", sql_query)
            
            # Check if a query is returned
            if sql_query:
                # Connect to the SQLite database
                connection = sqlite3.connect("F:/IBM/customerdata.db")
                cursor = connection.cursor()
                
                # Execute the generated SQL query
                cursor.execute(sql_query)
                
                # Fetch all rows from the result
                rows = cursor.fetchall()
                
                # Close the connection
                connection.close()
                
                # If data is returned, send it to the user
                if rows:
                    return jsonify({
                        "success": True,
                        "response": rows
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "No data found for the query."
                    })
            else:
                return jsonify({
                    "success": False,
                    "error": "No SQL query generated by Ollama."
                })
        else:
            return jsonify({
                "success": False,
                "error": f"Ollama API returned status code {response.status_code}"
            })
    
    except requests.RequestException as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
    except sqlite3.Error as e:
        return jsonify({
            "success": False,
            "error": f"SQLite error: {str(e)}"
        })

if __name__ == '__main__':
    app.run(debug=True)
