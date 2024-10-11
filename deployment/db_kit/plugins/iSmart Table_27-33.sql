DO $$
DECLARE
	plugin_name VARCHAR := 'iSmart Table';
	tool_id INT;
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- [persona:27,tool:ExcelAnalyzerTool,prompt:33]
    next_persona_id := nextval('persona_id_seq');
    
    
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)  
	VALUES (next_persona_id, 'iSmart Table', false, false, 'Analyze your excel data', 0, 'Meta-Llama-3-70B-Instruct', NULL, 'HYBRID', false, false, 'BASE_DECAY', true, NULL, '[]'::jsonb, true, 'lama-70b');
	
	SELECT id INTO tool_id FROM tool WHERE in_code_tool_id='ExcelAnalyzerTool'; 
	
    INSERT INTO public.persona__tool
    (persona_id, tool_id)
    VALUES(next_persona_id, tool_id);
	
    
    next_prompt_id := nextval('prompt_id_seq');

    INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted)
	VALUES (next_prompt_id, NULL, 'default-prompt__iSmart Table', 'Default prompt for persona iSmart Table', 'You are a knowledgeable excel analyzer, your job is to analyze the given excel document and answer the question.', '', true, false, true, false);
	
	
    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);
	

    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/Smart Table Analyzer.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": null, "supports_file_upload": true, "recommendation_prompt": {"task": "\"Instructions:\\n1. Review the provided input thoroughly\\n2. Generate simple questions which gives insights or statistics of given data file.\\n3. Ensure that each question is directly relevant to the information presented in the input and easy to answer.\\n4. For structured data (DataFrame):\\n             - Questions may relate to data distribution, correlations, potential data quality issues, or specific analyses that could be informative.\\n5. Strictly output the questions in the format: [\\\\\\\"Question1?\\\\\\\", \\\\\\\"Question2?\\\\\\\", ...], where each question is a string enclosed in double quotes, starting with a capital letter and ending with a question mark.\\n6. The output must be a valid JSON array of strings, without any additional text, headings, or explanations.\\n7. Do not include any additional text, headings, or explanations in response.\"", "system": "\"Given the input, generate a set of simple questions that can be used to further explore the information provided. The questions should be relevant to the key themes, concepts, entities, or data points present in the input.\\nContext: \\n**Data Input**:  {data_input}\""}, "custom_message_water_mark": "What is the average sales by city", "is_recommendation_supported": true, "supports_temperature_dialog": true}'::jsonb, NULL);

    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;