import { PluginInfo } from "@/app/admin/assistants/interfaces";
import { DEFAULT_ASSISTANT_INFO } from "../constants";

export async function fetchAssistantInfo(assistantId?: string | null): Promise<PluginInfo> {
    let assistantInfo: PluginInfo = DEFAULT_ASSISTANT_INFO;

    if (assistantId) {
        const response = await fetch(`/api/settings/plugin_info/${assistantId}`);
        if (response.ok) {
            assistantInfo = await response.json();
        }
    }
    return assistantInfo;
}
