DO $$
DECLARE
	plugin_name VARCHAR := 'HR English';
	tool_id INT;
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- [persona:28,tool:SearchTool,prompt:34]
    next_persona_id := nextval('persona_id_seq');
        
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
	VALUES (next_persona_id, 'HR English', false, false, 'Access HR Policies', 40, NULL, NULL, 'HYBRID', true, false, 'BASE_DECAY', true, NULL, '[{"name": "How many sick leave are allowed", "message": "How many sick leave are allowed", "description": "How many sick leave are allowed"}]'::jsonb, true, NULL);
	
	SELECT id INTO tool_id FROM tool WHERE in_code_tool_id='SearchTool'; 
	
    INSERT INTO public.persona__tool
    (persona_id, tool_id)
    VALUES(next_persona_id, tool_id);
				
    next_prompt_id := nextval('prompt_id_seq');
  
		
	INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted)
	VALUES (next_prompt_id, NULL, 'default-prompt__HR English', 'Default prompt for persona HR English', 'Your HR assistant, I have provided HR policy content, answer to your question based on provided content, don''t use your own knowledge to answer user question. If you don''t have answer, please ask for clarification. 
Always answer politely and professionally. Engage your with question and answer as much as you can.', 'Try to provide header or title based on user input question and answer. Make bullet points based on the context', true, false, true, false);

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);


    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/HR_English_Plugin.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": null, "supports_file_upload": false, "recommendation_prompt": {"task": "", "system": ""}, "custom_message_water_mark": "You can ask me questions about HR Policies.", "is_recommendation_supported": false, "supports_temperature_dialog": true}'::jsonb, NULL);

    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;