DO $$
DECLARE
	plugin_name VARCHAR := 'iTech Help - VMWare';
    next_persona_id INT;
    next_prompt_id INT;
BEGIN
    -- [persona:34,tool:null,prompt:40]
    next_persona_id := nextval('persona_id_seq');
    
   
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
	VALUES (next_persona_id, 'iTech Help - VMWare', false, false, 'Provides technical help for VMware related queries', 0, NULL, NULL, 'HYBRID', false, false, 'BASE_DECAY', true, NULL, '[]'::jsonb, true, NULL);

    next_prompt_id := nextval('prompt_id_seq');
   
		
	INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted)
	VALUES (next_prompt_id, NULL, 'default-prompt__iTech Help - VMWare', 'Default prompt for persona iTech Help - VMWare', 'You are a specialized assistant that helps users with tasks related to VMware virtualization. Your primary focus is on assisting with VMware products such as vSphere, ESXi, vCenter, and VMware Workstation. You should provide clear, concise, and technically accurate instructions, configurations, and solutions related to virtualization environments.
Do not answer questions related to political, entertainment,religion etc.', '', true, false, true, false);

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);	

    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/WMWare Plugin.svg", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "allowed_file_size": null, "supports_file_upload": false, "recommendation_prompt": {"task": "", "system": ""}, "custom_message_water_mark": "I can provide technical help for VMware related queries.", "is_recommendation_supported": false, "supports_temperature_dialog": true}'::jsonb, NULL);

    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;