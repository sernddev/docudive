export async function fetchAssistantInfo(assistantId?:number | null) {
    if(assistantId) {
        const response = await fetch(`/api/settings/plugin_info/${assistantId}`);

        if(response.ok) {
            const json = await response.json();
            return json;
        }
        return null;
    }
    return null;
}
