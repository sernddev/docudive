DO $$
DECLARE
	plugin_name VARCHAR := 'iExtract Answer';
BEGIN
    -- [persona:-2,tool:SearchTool,prompt:3]     
	UPDATE public.persona SET name='iExtract Answer', description='Extract the exact answer from the Connected Sources' WHERE id=-2;
	
    RAISE NOTICE 'Plugin % updated successfully',plugin_name;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Update Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;