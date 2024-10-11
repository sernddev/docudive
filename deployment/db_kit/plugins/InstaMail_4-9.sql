DO $$
DECLARE
	plugin_name VARCHAR := 'InstaMail';
	tool_id INT;
    next_persona_id INT;
    next_prompt_id INT;	
BEGIN
    -- [persona:4,tool:ComposeEmailTool,prompt:9]
    next_persona_id := nextval('persona_id_seq');
    
    
	INSERT INTO public.persona(id, "name", default_persona, deleted, description, num_chunks, llm_model_version_override, user_id, search_type, llm_relevance_filter, llm_filter_extraction, recency_bias, is_visible, display_priority, starter_messages, is_public, llm_model_provider_override)
	VALUES (next_persona_id, 'InstaMail', false, false, 'Draft professional emails', 0, 'Meta-Llama-3-70B-Instruct', NULL, 'HYBRID', false, false, 'BASE_DECAY', true, NULL, '[{"name": "طلب عقد اجتماع", "message": "هل يمكنك صياغة بريد إلكتروني يطلب فيه عقد اجتماع مع عميل محتمل يوم الثلاثاء المقبل لمناقشة خط الإنتاج الجديد لدينا؟", "description": "هل يمكنك صياغة بريد إلكتروني يطلب فيه عقد اجتماع مع عميل محتمل يوم الثلاثاء المقبل لمناقشة خط الإنتاج الجديد لدينا؟"}, {"name": " تذكير بالموعد النهائي", "message": "صغ بريدًا إلكترونيًا يذكر الفريق بالموعد النهائي القادم للتقرير ربع السنوي واطلب تحديثات الحالة", "description": "صغ بريدًا إلكترونيًا يذكر الفريق بالموعد النهائي القادم للتقرير ربع السنوي واطلب تحديثات الحالة"}, {"name": "إشعار بتغيير السياسة", "message": "يرجى كتابة بريد إلكتروني لإبلاغ جميع الموظفين بالسياسة الجديدة للعمل عن بُعد، وتضمين التغييرات الرئيسية وتواريخ التنفيذ", "description": "يرجى كتابة بريد إلكتروني لإبلاغ جميع الموظفين بالسياسة الجديدة للعمل عن بُعد، وتضمين التغييرات الرئيسية وتواريخ التنفيذ"}, {"name": "تأكيد اجتماع العميل", "message": "أنشئ بريدًا إلكترونيًا لتأكيد اجتماع مع العميل المقرر عقده يوم الجمعة المقبل، بما في ذلك الأجندة وتفاصيل الموقع", "description": "أنشئ بريدًا إلكترونيًا لتأكيد اجتماع مع العميل المقرر عقده يوم الجمعة المقبل، بما في ذلك الأجندة وتفاصيل الموقع"}]'::jsonb, true, 'lama-70b');
	
	
	SELECT id INTO tool_id FROM tool WHERE in_code_tool_id='ComposeEmailTool'; 

    INSERT INTO public.persona__tool
    (persona_id, tool_id)
    VALUES(next_persona_id, tool_id);
    
    next_prompt_id := nextval('prompt_id_seq');

    INSERT INTO public.prompt(id, user_id, "name", description, system_prompt, task_prompt, include_citations, datetime_aware, default_prompt, deleted)
	VALUES (next_prompt_id, NULL, 'default-prompt__InstaMail', 'Default prompt for persona InstaMail', 'You are an expert for composing context-aware emails. Analyze the user’s message to determine the email’s purpose and adjust tone and formality accordingly. Structure the email clearly, incorporating any specific details provided. Your goal is to help the user craft an email that is contextually appropriate and effective.
Always reply only in Arabic language except for my name in the closing of a mail. Use my name as it is and DO NOT translate it at the end of the mail.
While writing a comma in Arabic, use ، instead of ,

Always make sure to provide subject for the drafted email. 
Example for subject:
العنوان : الإجازة المرضية', '', true, false, true, false);

    INSERT INTO public.persona__prompt
    (persona_id, prompt_id)
    VALUES(next_persona_id, next_prompt_id);
	
    INSERT INTO public.key_value_store
    (key, value, encrypted_value)
	VALUES ('PLUGIN_INFO_'||next_persona_id, '{"image_url": "/static/icons/InstaMail.svg", "is_arabic": true, "is_favorite": false, "plugin_tags": null, "allowed_file_size": null, "supports_file_upload": false, "recommendation_prompt": {"task": "", "system": ""}, "custom_message_water_mark": "أنا هنا لمساعدتك في كتابة بريدك الإلكتروني التالي!", "is_recommendation_supported": false, "supports_temperature_dialog": true}'::jsonb, NULL);
    
    RAISE NOTICE 'Plugin % Inserted with ID %',plugin_name, next_persona_id;
EXCEPTION
    WHEN others THEN
        -- If there is any error, roll back
        ROLLBACK;
        RAISE NOTICE 'Failed to Insert Plugin % due to an error: %', plugin_name, SQLERRM;
END $$;