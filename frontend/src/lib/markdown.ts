import DOMPurify from "dompurify";
import { marked } from "marked";
import markedKatex from "marked-katex-extension";
import Prism from "prismjs";
import "prismjs/components/prism-python";

// Configured once for the app; marked.use() stacks extensions on every call.
marked.setOptions({
  highlight: (code: string, lang: string) =>
    Prism.languages[lang] ? Prism.highlight(code, Prism.languages[lang], lang) : code,
});
marked.use(markedKatex({ nonStandard: true }));

export const renderMarkdown = (text: string) => marked.parse(text);

// For markdown written by third parties, such as a skill's SKILL.md.
export const renderUntrustedMarkdown = (text: string) =>
  DOMPurify.sanitize(marked.parse(text));
