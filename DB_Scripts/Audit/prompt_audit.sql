CREATE TABLE public.prompt_audit (
id int4 NULL,
user_id uuid NULL,
"name" varchar NULL,
description varchar NULL,
system_prompt text NULL,
task_prompt text NULL,
include_citations bool NULL,
datetime_aware bool NULL,
default_prompt bool NULL,
deleted bool NULL,
operation varchar(12) NULL,
recupdated timestamp NULL DEFAULT CURRENT_TIMESTAMP
);

