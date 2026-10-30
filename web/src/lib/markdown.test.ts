import { describe, expect, it } from "vitest";
import { renderMarkdown } from "./markdown";

const hasKatex = (html: string) => html.includes('class="katex');

describe("renderMarkdown", () => {
  it("renders inline and display math", () => {
    expect(hasKatex(renderMarkdown("Time $O(n)$."))).toBe(true);
    expect(hasKatex(renderMarkdown("$$\\sum_i a_i$$"))).toBe(true);
  });

  it("leaves dollar signs in inline code alone", () => {
    const html = renderMarkdown("Use `$a + $b` in shell.");
    expect(hasKatex(html)).toBe(false);
    expect(html).toContain("<code>$a + $b</code>");
  });

  it("leaves dollar signs in fenced code alone", () => {
    const html = renderMarkdown("```bash\necho $HOME $PATH\n```");
    expect(hasKatex(html)).toBe(false);
    expect(html).toContain("echo $HOME $PATH");
  });

  it("renders markdown around math", () => {
    const html = renderMarkdown("**Bold** and $x$");
    expect(html).toContain("<strong>Bold</strong>");
    expect(hasKatex(html)).toBe(true);
  });
});
