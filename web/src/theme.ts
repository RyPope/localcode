export type Theme = "dark" | "light";
const KEY = "localcode.theme";

export function getTheme(): Theme {
  try {
    return localStorage.getItem(KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function applyTheme(t: Theme) {
  document.documentElement.classList.toggle("light", t === "light");
  try {
    localStorage.setItem(KEY, t);
  } catch {
    /* storage unavailable */
  }
  window.dispatchEvent(new CustomEvent("localcode-theme", { detail: t }));
}

/** Small persisted preference helper (language choice, split sizes). */
export function pref<T>(key: string, fallback: T): T {
  try {
    const v = localStorage.getItem(`localcode.${key}`);
    return v === null ? fallback : (JSON.parse(v) as T);
  } catch {
    return fallback;
  }
}

export function setPref(key: string, value: unknown) {
  try {
    localStorage.setItem(`localcode.${key}`, JSON.stringify(value));
  } catch {
    /* storage unavailable */
  }
}
