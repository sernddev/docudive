import { PluginInfo } from "@/app/admin/assistants/interfaces";

export async function fetchAssistantInfo(assistantId?: number | null): Promise<PluginInfo> {
    let assistantInfo: PluginInfo = {}

    if (assistantId) {
        const response = await fetch(`/api/settings/plugin_info/${assistantId}`);
        if (response.ok) {
            assistantInfo = await response.json();
        }
    }
    return assistantInfo;
}
