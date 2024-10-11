DO $$
DECLARE
	plugin_name VARCHAR := 'Knowledge Publisher';
BEGIN
    -- persona:0,tool:SearchTool,prompt:0]   
	UPDATE public.persona SET name='Knowledge Publisher', description='Access the documents from your Connected Sources' WHERE id=0;
	
	RAISE NOTICE 'Plugin % updated successfully',plugin_name;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Update Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;