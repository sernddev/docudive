import { Persona } from "@/app/admin/assistants/interfaces";
import { fetchSS } from "../utilsSS";
import { isValidImageUrl } from "../fetchUtils";

export type FetchAssistantsResponse = [Persona[], string | null];
export type FetchAssistantIconsResponse = {[key: string]: string};

export async function fetchAssistantsSS(): Promise<FetchAssistantsResponse> {
  const response = await fetchSS("/persona");
  if (response.ok) {
    return [(await response.json()) as Persona[], null];
  }
  return [[], (await response.json()).detail || "Unknown Error"];
}

export async function fetchAssistantIconsSS(): Promise<FetchAssistantIconsResponse> {
  const response = await fetchSS("/settings/image_url");
  let images: FetchAssistantIconsResponse = {};
  if (response.ok) {
    images =  await response.json();
    for( const key in images) {
      if(!images[key] || !images[key]?.trim()) {
          delete images[key];
      }
    }
    return images;
  }

  return images;
}