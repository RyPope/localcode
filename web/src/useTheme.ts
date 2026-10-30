import { useEffect, useState } from "react";
import { getTheme, type Theme } from "./theme";

export function useTheme(): Theme {
  const [t, setT] = useState<Theme>(getTheme());
  useEffect(() => {
    const on = (e: Event) => setT((e as CustomEvent<Theme>).detail);
    window.addEventListener("localcode-theme", on);
    return () => window.removeEventListener("localcode-theme", on);
  }, []);
  return t;
}
