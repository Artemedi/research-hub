# BK-064 — bounded independent generator probe (NOT a live DeepSeek Harness Creator Mode session)

This is a single safe development attempt using an offline workspace. You are creating the **Client half** of a dynamic Cordis Plugin for an isolated unit harness, not installing or running it on the real DSH runtime.

## Exact official request
Create a poster design workbench plugin accessible from the conversation. Use the shader background pattern and English font from the DeepSeek Harness website. Let me customize the poster title, text, and shader colors. Keep the default page minimal, with no unnecessary subheadings or information. Set the default poster title to “Everything is a plugin”.

## Verified contract excerpt (source: deepseek-harness@5b9d438, cordis-plugin-development/SKILL.md)
- Client code consists of a plain JavaScript **function body** returning an object-form Cordis Plugin `return { apply(ctx) { ... } }`. No import, require, JSX, TypeScript or Node globals.
- React and styles are evaluator-provided closure symbols. Use `React.createElement(...)` with `React.useState` for controls, and optional `styles.insert(css)` (returns disposer).
- For a UI displayed in the latest Creator Run card, known supported target: `slots.inject('tool.view.cordis', () => slots.register({ name: 'tool.view.cordis', key: 'self' }, Component))`; query of live provider is *not available* in this offline test, so this is constrained to the documented Run card, not an arbitrary conversation sidebar.
- Obtain slots through `const slots = ctx.get('slots'); if (!slots) return`. Retain disposer via `ctx.effect(() => slots.inject(...))` only if necessary; no process or page global effects.
- The code will be evaluated in an isolated Node VM/container with a synthetic slots service, NOT a real DSH browser. Avoid DOM/browser/process/fetch/timers/global libraries. Do not access filesystem or network.
- No actual logo/font/shader asset from DeepSeek website is provided. Use a CSS-only gradient/shader approximation and a system sans-serif English typeface, and disclose this deviation.

## Output
Write **exactly** two files inside this workspace:
1. `code.client.js` — function body returning a Cordis client plugin. UI with default title, editable title, text, two or more independent gradient/shader colors, minimal default layout, clear render elements with form controls; no external API.
2. `manifest.json` — fields `id`, `intent`, `exactWebsiteShaderAndFont` (false), `scope` ("offline client-only Cordis Run card"), `knownLimitations` (array).
Do not write or modify any other file. Do NOT execute code, install dependencies, call a web API, read local credentials, or interact with any other path. Keep output compact.
