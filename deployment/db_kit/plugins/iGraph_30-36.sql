DO $$
DECLARE
	plugin_name VARCHAR := 'iGraph';
	tool_id INT;
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- [persona:30,tool:FileDataInfographicsTool,prompt:36]
    next_persona_id := nextval('persona_id_seq');
       
	
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
    VALUES (next_persona_id, 'iGraph', false, false, 'Analyze your data with Infographs ', 0, 'Meta-Llama-3-70B-Instruct', NULL, 'HYBRID', false, false, 'BASE_DECAY', true, NULL, '[]'::jsonb, true, 'lama-70b');
		
	SELECT id INTO tool_id FROM tool WHERE in_code_tool_id='FileDataInfographicsTool'; 
	
    INSERT INTO public.persona__tool
    (persona_id, tool_id)
    VALUES(next_persona_id, tool_id);
	
    
    next_prompt_id := nextval('prompt_id_seq');

    
    INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted)
	VALUES (next_prompt_id, NULL, 'default-prompt__iGraph', 'Default prompt for persona iGraph', 'SQL Query Results and Schema Context:**         Given the SQL query results and database schema, identify the appropriate fields for creating a visualization using Plotly. The output should directly match the SQL query structure, considering all selected fields.         **SQL Query:**         {sql_query}         **Database Schema:**         {schema}         **Chart Type:**         {chart_type}         **User Requirements:**         {requirement}            \n The user aims to visualize data related to the SQL query focused on requirement, requiring a comprehensive representation of all fields used in the SQL query for aggregations, computations, or groupings.\n            **Expected Fields from SQL Query:**         - Ensure that the number of fields suggested corresponds exactly to the number of columns returned by the SQL query.         - The fields should be listed in the order they appear in the SQL query results and presented in a dictionary format appropriate to the chart type.    ', '**Guidelines for Suggesting Fields:**         - For PIE, BAR, and HEATMAP charts, suggest fields for ''x'' and ''y'' and return dictionary like {{\"x\": \"\", \"y\": \"\"}}.         - For SCATTER charts, suggest fields for ''x'', ''y'', and ''color'' and return dictionary like {{\"x\": \"\", \"y\": \"\", \"color\": \"\"}}.         - For SCATTER_MATRIX charts, suggest fields for ''x'', ''y'', ''color'', and ''size'' and return dictionary like {{\"x\": \"\", \"y\": \"\", \"color\": \"\", \"size\": \"\"}}.                 - Ensure the ''size'' parameter must be a numeric field; if the initially suggested ''size'' is not numeric, suggest the next available numeric field from the database.         - If no suitable numeric field is available for ''size'', reconsider the roles of ''x'' and ''y'' to ensure they are optimally assigned.         - Analyze columns properly to suggest the right match for each parameter, especially for SCATTER_MATRIX:           - ''x'' and ''y'' should be chosen based on their ability to represent dimensions.           - ''color'' should ideally be a categorical variable.           - ''size'' must be a numeric column, suitable for quantifying or scaling markers.         - Avoid assumptions; ensure the suggested fields match the actual data types required for each chart parameter.         - Do not include any explanations or additional text.         **Output:**         Provide suggestions in a dictionary format, ensuring all suggestions align with the type of visualization to effectively convey the intended insights and reflect the data structure accurately.         ', true, false, true, false);

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);
	
    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/Smart Chart.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": 300, "supports_file_upload": true, "recommendation_prompt": {"task": "\"\\\\nInstructions:\\\\n \\\\n    1. Review the provided input thoroughly, whether it is structured (e.g., DataFrame schema and sample data) or unstructured (e.g., text, PDF).\\\\n \\\\n    2. Generate simple and easy-to-answer questions that aid in exploring basic relationships, trends, and patterns using graphs.\\\\n \\\\n    3. Ensure that no questions are related to dates and that all generated questions can be answered using graphical visualizations like bar charts, scatter plots, scatter matrix.  \\\\n\\\\n   4. Avoid complex or multi-step analyses. Focus on questions that can be addressed with straightforward visualizations.  \\\\n \\\\n    5. For structured data (DataFrame):\\\\n \\\\n       - Questions may relate to data distribution, correlations, potential data quality issues, or specific analyses that could be informative.\\\\n \\\\n \\\\n       For unstructured content (Text or PDF):\\\\n \\\\n       - Questions may relate to key themes, potential inconsistencies, missing information, or areas that require further exploration.\\\\n \\\\n \\\\n    5. Strictly output the questions in the format: [\\\\\\\"Question1?\\\\\\\", \\\\\\\"Question2?\\\\\\\", ...], where each question is a string enclosed in double quotes, starting with a capital letter and ending with a question mark.\\\\n \\\\n    6. The output must be a valid JSON array of strings, without any additional text, headings, or explanations.\\\\n \\\\n    7. Do not include any additional text, headings, or explanations in response\\\\n\"", "system": "\" \\\\nGiven structured data (e.g., a DataFrame) or unstructured content (e.g., a PDF or text file), \\\\n\\\\n generate a simple set of insightful questions focused on visual exploration through graphs. \\\\n \\\\n  These questions should help identify key trends, relationships, and patterns within the data. Avoid generating complex or difficult questions. Keep the questions relevant to straightforward analyses and easy-to-interpret visualizations.\\\\n \\\\n    Context:           \\\\n \\\\n     - **Data Input:** \\\\n \\\\n  {data_input}\\\\n\""}, "custom_message_water_mark": "Send a message", "is_recommendation_supported": true, "supports_temperature_dialog": true}'::jsonb, NULL);
	
	
    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;