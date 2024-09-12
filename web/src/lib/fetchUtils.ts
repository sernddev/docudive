export const getErrorMsg = async (response: Response) => {
  if (response.ok) {
    return null;
  }
  const responseJson = await response.json();
  return responseJson.message || responseJson.detail || "Unknown error";
};


export function isValidImageUrl(urlString: string) {
  try {
    const url = new URL(urlString);

    return /\.(jpg|jpeg|png|gif|svg)$/i.test(url.pathname);
  } catch (error) {
    return false;
  }
}