import { PluginInfo } from "@/app/admin/assistants/interfaces";
import { DEFAULT_ASSISTANT_INFO } from "../constants";

export async function fetchAssistantInfo(url:string): Promise<PluginInfo> {
    let assistantInfo: PluginInfo = DEFAULT_ASSISTANT_INFO;
    try {
        const response = await fetch(url);
        if (response.ok) {
            assistantInfo = await response.json();
        }
    } catch(e) {
        return Promise.resolve(assistantInfo);
    }
    
    return Promise.resolve(assistantInfo);
}
