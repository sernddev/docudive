import { isValidImageUrl } from "../fetchUtils";

export async function fetchAssistantIcon(assistantId?:number | null) {
    if(assistantId) {
        const response = await fetch(`/api/settings/image_url/${assistantId}`);

        if(response.ok) {
            const json = await response.json();
            if(json) {
                return json;
            }
        } 
        return "";
    } else {
        const res = await fetch('/api/settings/image_url');
        const images = await res.json();
        for( const key in images) {
            if(!images[key] || !images[key]?.trim()) {
                delete images[key];
            }
        }

        return images;
    }
}
