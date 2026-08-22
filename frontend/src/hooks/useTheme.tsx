import { createContext, useContext, useEffect } from "react";
import type { ReactNode } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue>({ theme: "system", setTheme: () => undefined });

const THEME_KEY = "mindvault-theme";

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const stored = (localStorage.getItem(THEME_KEY) as Theme | null) ?? "system";
  useEffect(() => {
    applyTheme(stored);
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => applyTheme(stored);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [stored]);

  const setTheme = (t: Theme) => {
    localStorage.setItem(THEME_KEY, t);
    applyTheme(t);
    window.dispatchEvent(new CustomEvent("mindvault-theme", { detail: t }));
  };

  return <ThemeContext.Provider value={{ theme: stored, setTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
