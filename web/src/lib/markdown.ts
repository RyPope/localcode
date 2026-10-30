import katex from "katex";
import { marked } from "marked";

const CODE = /```[\s\S]*?```|`[^`\n]+`/g;
const DISPLAY_MATH = /\$\$([\s\S]+?)\$\$/g;
const INLINE_MATH = /\$([^$\n]+?)\$/g;

/**
 * Markdown to HTML with `$inline$` and `$$display$$` math rendered by KaTeX.
 * Code spans and fenced blocks are left untouched, so `$` inside code is never treated as math.
 * The result is not sanitised; callers must pass it through DOMPurify before inserting it.
 */
export function renderMarkdown(src: string): string {
  const code: string[] = [];
  const math: string[] = [];
  const tex = (s: string, displayMode: boolean) => katex.renderToString(s, { throwOnError: false, displayMode });

  const withoutCode = src.replace(CODE, (m) => `@@CODE${code.push(m) - 1}@@`);
  const withMath = withoutCode
    .replace(DISPLAY_MATH, (_, s: string) => `@@MATH${math.push(tex(s, true)) - 1}@@`)
    .replace(INLINE_MATH, (_, s: string) => `@@MATH${math.push(tex(s, false)) - 1}@@`);
  const restored = withMath.replace(/@@CODE(\d+)@@/g, (_, i: string) => code[Number(i)]);
  const html = marked.parse(restored, { async: false }) as string;
  return html.replace(/@@MATH(\d+)@@/g, (_, i: string) => math[Number(i)]);
}
