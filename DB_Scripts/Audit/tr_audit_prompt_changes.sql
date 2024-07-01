CREATE OR replace TRIGGER tr_audit_prompt_changes
              BEFORE INSERT OR UPDATE OR DELETE ON public.prompt
    FOR EACH ROW
EXECUTE FUNCTION public.log_prompt_changes();


CREATE OR REPLACE FUNCTION public.log_prompt_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
INSERT INTO public.prompt_audit (
    id, user_id, name, description, system_prompt,
    task_prompt, include_citations, datetime_aware,
    default_prompt, deleted, operation
) VALUES (
             NEW.id, NEW.user_id, NEW.name, NEW.description, NEW.system_prompt,
             NEW.task_prompt, NEW.include_citations, NEW.datetime_aware,
             NEW.default_prompt, NEW.deleted, 'INSERT'
         );
RETURN NEW;
ELSIF (TG_OP = 'UPDATE') THEN
INSERT INTO public.prompt_audit (
    id, user_id, name, description, system_prompt,
    task_prompt, include_citations, datetime_aware,
    default_prompt, deleted, operation
) VALUES (
             NEW.id, NEW.user_id, NEW.name, NEW.description, NEW.system_prompt,
             NEW.task_prompt, NEW.include_citations, NEW.datetime_aware,
             NEW.default_prompt, NEW.deleted, 'UPDATE'
         );
RETURN NEW;
ELSIF (TG_OP = 'DELETE') THEN
INSERT INTO public.prompt_audit (
    id, user_id, name, description, system_prompt,
    task_prompt, include_citations, datetime_aware,
    default_prompt, deleted, operation
) VALUES (
             OLD.id, OLD.user_id, OLD.name, OLD.description, OLD.system_prompt,
             OLD.task_prompt, OLD.include_citations, OLD.datetime_aware,
             OLD.default_prompt, OLD.deleted, 'DELETE'
         );
RETURN OLD;
END IF;
END;
$$ LANGUAGE plpgsql;
