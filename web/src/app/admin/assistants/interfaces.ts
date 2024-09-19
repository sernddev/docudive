import { ToolSnapshot } from "@/lib/tools/interfaces";
import { DocumentSet, MinimalUserSnapshot } from "@/lib/types";

export interface StarterMessage {
  name: string;
  description: string | null;
  message: string;
}

export interface Prompt {
  id: number;
  name: string;
  description: string;
  system_prompt: string;
  task_prompt: string;
  include_citations: boolean;
  datetime_aware: boolean;
  default_prompt: boolean;
}

export interface Persona {
  id: number;
  name: string;
  owner: MinimalUserSnapshot | null;
  is_visible: boolean;
  is_public: boolean;
  display_priority: number | null;
  description: string;
  document_sets: DocumentSet[];
  prompts: Prompt[];
  tools: ToolSnapshot[];
  num_chunks?: number;
  icon?: string;
  llm_relevance_filter?: boolean;
  llm_filter_extraction?: boolean;
  llm_model_provider_override?: string;
  llm_model_version_override?: string;
  starter_messages: StarterMessage[] | null;
  default_persona: boolean;
  users: MinimalUserSnapshot[];
  groups: number[];
}

export interface PluginInfo{
  image_url?: string;
  plugin_tags?: string[];
  supports_file_upload?: boolean;
  supports_temperature_dialog?: boolean;
  custom_message_water_mark?: string;
  is_recommendation_supported?: boolean;
  is_favorite?:boolean;
  recommendation_prompt?: string;
  is_arabic?:boolean;
}
