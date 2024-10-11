DO $$
DECLARE
	plugin_name VARCHAR := 'iSummarize';
	tool_id INT;
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- [persona:3,tool:SummaryGenerationTool,prompt:6]
    next_persona_id := nextval('persona_id_seq');
    
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
	VALUES (next_persona_id, 'iSummarize', false, false, 'Summarize the large text or file', 0, 'Meta-Llama-3-70B-Instruct', NULL, 'HYBRID', false, false, 'BASE_DECAY', true, NULL, '[]'::jsonb, true, 'lama-70b');

	SELECT id INTO tool_id FROM tool WHERE in_code_tool_id='SummaryGenerationTool'; 
	
    INSERT INTO public.persona__tool
    (persona_id, tool_id)
    VALUES(next_persona_id, tool_id);
	
    
    next_prompt_id := nextval('prompt_id_seq');

	INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted)
	VALUES (next_prompt_id, NULL, 'default-prompt__iSummarize', 'Default prompt for persona iSummarize', 'Summarize the provided text, capturing the main ideas and key points while maintaining clarity and coherence.
Avoid jargon and complex language. Ensure the summary is accessible to general audience.
Keep it short.', 'You''re a summarization assistant, summarize the given text professionally.
DO NOT start with any texts like ''Here is a summary of the text:'' at the beginning of the response.', true, false, true, false);
		

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);


    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/Paraphrase.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": 10, "supports_file_upload": true, "recommendation_prompt": {"task": "", "system": ""}, "custom_message_water_mark": "Hi! I can help you summarize large text.", "is_recommendation_supported": false, "supports_temperature_dialog": true}'::jsonb, NULL);

    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;