import { useCallback, useState } from "react";
import { pref, setPref } from "../theme";

/**
 * Draggable split between two panes. `size` is the first pane's share (0–1) of the container
 * along `axis`; it is persisted under `key`.
 */
export function useSplit(key: string, initial: number, axis: "x" | "y", min = 0.2, max = 0.8) {
  const [size, setSize] = useState<number>(() => pref(key, initial));
  // A callback ref kept in state, so render only ever reads plain values.
  const [element, container] = useState<HTMLElement | null>(null);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      const box = element?.getBoundingClientRect();
      if (!box) return;
      let last = size;
      const move = (ev: PointerEvent) => {
        const ratio = axis === "x" ? (ev.clientX - box.left) / box.width : (ev.clientY - box.top) / box.height;
        last = Math.min(max, Math.max(min, ratio));
        setSize(last);
      };
      const up = () => {
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", up);
        document.body.style.cursor = "";
        setPref(key, last);
      };
      document.body.style.cursor = axis === "x" ? "col-resize" : "row-resize";
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
    },
    [axis, element, key, max, min, size],
  );

  return { size, container, onPointerDown };
}
