DO $$
BEGIN
	UPDATE public.persona SET is_public = false;
    RAISE NOTICE 'All plugins 'is_public' column set to false successfully';
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Update Persona';
END $$;