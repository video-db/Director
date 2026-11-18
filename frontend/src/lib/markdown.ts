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
