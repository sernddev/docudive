
export function getSelectedModal() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem("selectedModel");
  }
}

export function sendSelectedModal(data:any) {
  if (typeof window !== 'undefined') {
    localStorage.setItem("selectedModel", data);
  }
}
