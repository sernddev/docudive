DO $$
DECLARE
	plugin_name VARCHAR := 'GPT';
BEGIN
    -- [persona:-1,tool:null,prompt:1]      
	UPDATE public.persona SET description='Access the Global General Knowledge from the LLM' WHERE id=-1;
	
	INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_-1', '{"image_url": "", "is_arabic": false, "is_favorite": false, "plugin_tags": null, "supports_file_upload": false, "recommendation_prompt": null, "custom_message_water_mark": "Ask your question here", "is_recommendation_supported": false, "supports_temperature_dialog": true}'::jsonb, NULL);
	
  
    RAISE NOTICE 'Plugin % updated successfully',plugin_name;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Update Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;