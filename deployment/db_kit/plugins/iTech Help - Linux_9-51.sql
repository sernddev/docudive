DO $$
DECLARE
	plugin_name VARCHAR := 'iTech Help - Linux';	
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- Plugin "iTech Help - Linux" [persona:9,tool:null,prompt:51]
    next_persona_id := nextval('persona_id_seq');
    

	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
	VALUES (next_persona_id, 'iTech Help - Linux', false, false, 'Provides technical help for Linux related queries', 0, 'Meta-Llama-3-70B-Instruct', NULL, 'HYBRID', false, false, 'BASE_DECAY', true, NULL, '[{"name": "Give me some commonly used command related to RHEL", "message": "Give me the most common commands related to Red Hat enterprise Linux", "description": "List of most common used commands of RHEL"}, {"name": "How to create a new user in Redhat Linux", "message": "How to create a new user in Redhat ?", "description": "How to create a new user in Redhat Linux"}, {"name": "How to deploy an application in Oracle Linux ( OEM)", "message": "How to deploy an application in Oracle Linux ( OEM)", "description": "How to deploy an application in Oracle Linux ( OEM)"}, {"name": "What are some advantages of Red Hat Linux?", "message": "What are some advantages of Red Hat Linux?", "description": "What are some advantages of Red Hat Linux?"}]'::jsonb, true, 'lama-70b');
	
	next_prompt_id := nextval('prompt_id_seq');
  		
	INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted) 
	VALUES (next_prompt_id, NULL, 'default-prompt__iTech Help - Linux', 'Default prompt for persona iTech Help - Linux', 'You are a highly knowledgeable Linux expert. Your role is to provide accurate, detailed, and practical advice on Linux operating systems, commands, configurations, and troubleshooting. 
	Always prioritize clarity and conciseness in your explanations. If a question is ambiguous, ask for clarification to ensure you provide the most relevant information.
	', '', true, false, true, false);

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);


    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/Linux_Plugin.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": null, "supports_file_upload": false, "recommendation_prompt": {"task": "", "system": ""}, "custom_message_water_mark": "Ask any linux related questions!", "is_recommendation_supported": false, "supports_temperature_dialog": true}'::jsonb, NULL);

    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;