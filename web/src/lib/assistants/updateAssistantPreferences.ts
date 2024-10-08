import { PluginInfo } from "@/app/admin/assistants/interfaces";

async function updateUserAssistantList(
  chosenAssistants: number[]
): Promise<boolean> {
  const response = await fetch("/api/user/assistant-list", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ chosen_assistants: chosenAssistants }),
  });

  return response.ok;
}

export async function removeAssistantFromList(
  assistantId: number,
  chosenAssistants: number[]
): Promise<boolean> {
  const updatedAssistants = chosenAssistants.filter((id) => id !== assistantId);
  return updateUserAssistantList(updatedAssistants);
}

export async function addAssistantToList(
  assistantId: number,
  chosenAssistants: number[]
): Promise<boolean> {
  if (!chosenAssistants.includes(assistantId)) {
    const updatedAssistants = [...chosenAssistants, assistantId];
    return updateUserAssistantList(updatedAssistants);
  }
  return false;
}

export async function saveAssistantInfo(assistantId: number, pluginInfo: PluginInfo) {
  
  pluginInfo.allowed_file_size = pluginInfo.allowed_file_size ?? undefined;
    
  const requestOptions = {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pluginInfo)
    }  
    const response = await fetch(`/api/settings/plugin_info/${assistantId}`, requestOptions);

    if(response.ok) {
      return await response.json();
    } else {
      return false;
    }
}
export async function moveAssistantUp(
  assistantId: number,
  chosenAssistants: number[]
): Promise<boolean> {
  const index = chosenAssistants.indexOf(assistantId);
  if (index > 0) {
    [chosenAssistants[index - 1], chosenAssistants[index]] = [
      chosenAssistants[index],
      chosenAssistants[index - 1],
    ];
    return updateUserAssistantList(chosenAssistants);
  }
  return false;
}

export async function moveAssistantDown(
  assistantId: number,
  chosenAssistants: number[]
): Promise<boolean> {
  const index = chosenAssistants.indexOf(assistantId);
  if (index < chosenAssistants.length - 1) {
    [chosenAssistants[index + 1], chosenAssistants[index]] = [
      chosenAssistants[index],
      chosenAssistants[index + 1],
    ];
    return updateUserAssistantList(chosenAssistants);
  }
  return false;
}
