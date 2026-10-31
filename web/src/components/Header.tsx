import { useEffect, useRef, useState } from "react";
import { ICONS } from "../lib/icons";
import { NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";
import { applyTheme, getTheme } from "../theme";
import { SearchInput } from "./layout";
import { Icon } from "./ui";

export default function Header() {
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        input.current?.focus();
        input.current?.select();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function jump(e: React.FormEvent) {
    e.preventDefault();
    const text = q.trim();
    if (!text) return;
    const r = await api.problems({ q: text, page_size: 2 });
    if (r.items.length === 1 || /^\d+$/.test(text)) {
      if (r.items[0]) nav(`/problems/${r.items[0].slug}`);
    } else {
      nav(`/?q=${encodeURIComponent(text)}`);
    }
    setQ("");
    input.current?.blur();
  }

  return (
    <header className="hdr">
      <NavLink to="/" className="logo" aria-label="localcode home">
        <span className="logo-mark">
          <Icon d={ICONS.logo} stroke={2.6} />
        </span>
        <span className="logo-text">localcode</span>
      </NavLink>
      <nav aria-label="Primary">
        <NavLink className="navlink" to="/" end>
          Problems
        </NavLink>
        <NavLink className="navlink" to="/companies">
          Companies
        </NavLink>
        <NavLink className="navlink" to="/progress">
          Progress
        </NavLink>
      </nav>
      <div className="spacer" />
      <form className="hdr-search" onSubmit={jump}>
        <SearchInput
          id="jump"
          label="Jump to problem"
          placeholder="Jump to problem…"
          value={q}
          onChange={setQ}
          inputRef={input}
          trailing={<span className="kbd">⌘K</span>}
        />
      </form>
      <span className="mono hdr-host">
        <span className="dot" />
        {window.location.host}
      </span>
      <button
        className="btn ghost ibtn"
        aria-label="Toggle light or dark theme"
        onClick={() => applyTheme(getTheme() === "dark" ? "light" : "dark")}
      >
        <Icon d={ICONS.sun} size={15} />
      </button>
    </header>
  );
}
