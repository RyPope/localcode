import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";
import { applyTheme, getTheme } from "../theme";
import { Icon, ICONS } from "./ui";

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
      <NavLink to="/" className="logo">
        <span className="logo-mark"><Icon d={ICONS.logo} stroke={2.6} /></span>
        localcode
      </NavLink>
      <nav aria-label="Primary" style={{ display: "flex", gap: 2 }}>
        <NavLink className="navlink" to="/" end>Problems</NavLink>
        <NavLink className="navlink" to="/companies">Companies</NavLink>
        <NavLink className="navlink" to="/progress">Progress</NavLink>
      </nav>
      <div style={{ flex: 1 }} />
      <form onSubmit={jump} style={{ position: "relative", width: 280 }}>
        <label className="sr" htmlFor="jump">Jump to problem</label>
        <span style={{ position: "absolute", left: 10, top: 8, color: "var(--fg3)" }}><Icon d={ICONS.search} /></span>
        <input id="jump" ref={input} className="inp icon" placeholder="Jump to problem…" value={q}
          onChange={(e) => setQ(e.target.value)} autoComplete="off" />
        <span className="kbd" style={{ position: "absolute", right: 8, top: 7 }}>⌘K</span>
      </form>
      <span className="mono muted" style={{ fontSize: 11.5, display: "flex", alignItems: "center", gap: 6 }}>
        <span className="dot" style={{ background: "var(--easy)", width: 6, height: 6 }} />
        {window.location.host}
      </span>
      <button className="btn ghost ibtn" aria-label="Toggle light or dark theme"
        onClick={() => applyTheme(getTheme() === "dark" ? "light" : "dark")}>
        <Icon d={ICONS.sun} size={15} />
      </button>
    </header>
  );
}
