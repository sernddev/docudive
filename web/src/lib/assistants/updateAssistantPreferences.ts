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

export async function saveIconsForAssistants(assistantId: number, imageURL: string) {
    const body = {"key":assistantId , "value": imageURL};  
    const requestOptions = {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }  
    const response = await fetch('/api/settings/image_url', requestOptions);

    if(response.ok) {
      return await response.json();
    } else {
      return false;
    }
}
function isValidImageUrl(urlString: string) {
  try {
    const url = new URL(urlString);

    return /\.(jpg|jpeg|png|gif|svg)$/i.test(url.pathname);
  } catch (error) {
    return false;
  }
}

export async function getAssitantServerIcon(assistantId: number) {
  const response = await fetch(`/api/settings/image_url/${assistantId}`);

  if(response.ok) {
    const json = await response.json();
    if(json.value && isValidImageUrl(json.value)) {
      return json.value;
    }
  }

  return "";
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
