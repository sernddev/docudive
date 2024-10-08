import { ALLOWED_FILE_CATEGORY } from "./constants";
import { Cache, State } from 'swr';

export function localStorageProviderForSWR(
  cache: Readonly<Cache<any>>
): Cache<State<any, any>> {

  let parsed: [string, State<any, any>][] = [];
  const appCache = localStorage?.getItem('app-cache');

  if (appCache) {
    parsed = JSON.parse(appCache);
  }

  const map = new Map<string, State<any, any>>(parsed);

  if (cache && cache.keys) {
    const keysArray = Array.from(cache.keys());
    for (const key of keysArray) {
      const value = cache.get(key);
      if (value !== undefined) {
        map.set(key, value);
      }
    }
  }

  window.addEventListener('beforeunload', () => {
    const appCache = JSON.stringify(Array.from(map.entries()));
    localStorage?.setItem('app-cache', appCache);
  });

  return {
    get(key: string): State<any, any> | undefined {
      return map.get(key);
    },
    set(key: string, value: State<any, any>) {
      map.set(key, value);
    },
    delete(key: string) {
      map.delete(key);
    },
    keys(): IterableIterator<string> {
      return map.keys();
    },
  };
}

export function getFileExtension(filename:string) {
    return filename.split('.').pop()?.toLocaleLowerCase();
}
  
export function isAllowedFileType(filename: string, category?: ALLOWED_FILE_CATEGORY[]): [boolean, string] {
  
    const allowedTypes = Object.values(
      category?.length ? 
        category:
        ALLOWED_FILE_CATEGORY
    ).join().split(/\s*,\s*/);
    const extension = getFileExtension(filename);

    return (
        extension ? 
            [allowedTypes.includes(extension), extension]: 
            [false, ""]
    );
  }

export function fallbackCopyTextToClipboard(text: string) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
      document.execCommand('copy');
    } catch (err) {
      console.error('Fallback: Oops, unable to copy', err);
    }
    
    document.body.removeChild(textArea);
  }
  