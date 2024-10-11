DO $$
DECLARE
	plugin_name VARCHAR := 'iQuestion';
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- [persona:25,tool:null,prompt:31]
    next_persona_id := nextval('persona_id_seq');
    
    
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
	VALUES (next_persona_id, 'iQuestion', false, false, 'Chat with your documents', 0, NULL, NULL, 'HYBRID', true, false, 'BASE_DECAY', true, NULL, '[]'::jsonb, true, NULL);


    next_prompt_id := nextval('prompt_id_seq');

    INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted) 
    VALUES (next_prompt_id, NULL, 'default-prompt__iQuestion', 'Default prompt for persona iQuestion', 'You are a knowledgeable assistant capable of understanding and processing natural language. Your task is to read a provided context from a text file and answer a specific question based on that context. Please follow these steps:

Read the Context: You will receive a block of text that provides background information. Read and comprehend this text carefully.
Answer the Question: After reading the context, you will be asked a question related to it. Your answer should be concise, relevant, and based on the information provided in the context.
Clarification: If the question is unclear or cannot be answered based on the context, indicate that additional information is needed.

DO NOT use your existing knowledge to answer questions.', '', true, false, true, false);
		

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);
	
    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/Q&A.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": null, "supports_file_upload": true, "recommendation_prompt": {"task": "\"\\\\nInstructions:\\\\n \\\\n    1. Review the provided input thoroughly, whether it is structured (e.g., DataFrame schema and sample data) or unstructured (e.g., text, PDF).\\\\n \\\\n    2. Generate questions that help the user with some sample questions based on input data.\\\\n \\\\n    3. Ensure that each question is directly relevant to the information presented in the input.\\\\n \\\\n    4. For structured data (DataFrame):\\\\n \\\\n       - Questions may relate to data distribution, correlations, potential data quality issues, or specific analyses that could be informative.\\\\n \\\\n \\\\n       For unstructured content (Text or PDF):\\\\n \\\\n       - Questions may relate to key themes, missing information, or searching for information in the input.\\\\n \\\\n \\\\n    5. Strictly output the questions in the format: [\\\\\\\"Question1?\\\\\\\", \\\\\\\"Question2?\\\\\\\", ...], where each question is a string enclosed in double quotes, starting with a capital letter and ending with a question mark.\\\\n \\\\n    6. The output must be a valid JSON array of strings, without any additional text, headings, or explanations.\\\\n \\\\n    7. Do not include any additional text, headings, or explanations in response\\\\n\"", "system": "\"\\\\nGiven the input, whether it''s structured data (e.g., a DataFrame) or unstructured content (e.g., a PDF or text file), \\\\n \\\\n    generate a set of insightful questions that can be used to further explore the information provided. \\\\n \\\\n    The questions should be relevant to the key themes, concepts, entities, or data points present in the input.\\\\n \\\\n    Context:\\\\n \\\\n    - **Data Input:**\\\\n \\\\n        {data_input}\\\\n\""}, "custom_message_water_mark": "Please ask me a question!", "is_recommendation_supported": true, "supports_temperature_dialog": true}'::jsonb, NULL);

    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;