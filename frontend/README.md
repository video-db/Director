# 🎬 Director Frontend

The chat app for Director: Vue 3 + TypeScript, Vue Router, Pinia and Tailwind, talking to the backend over HTTP and socket.io.

## Getting started

From the repo root, `make install-fe` then `make run-fe`. Or from this folder:

```bash
npm install
cp .env.sample .env   # point VITE_APP_BACKEND_URL at the backend
npm run dev
```

| Script | What it does |
|---|---|
| `npm run dev` | Dev server on `VITE_PORT` (default 8080) |
| `npm run build` | Type-check, then build to `dist/` |
| `npm run typecheck` | `vue-tsc --noEmit` |
| `npm test` | Vitest |

| Env var | Default |
|---|---|
| `VITE_APP_BACKEND_URL` | `http://127.0.0.1:8000` |
| `VITE_PORT` | `8080` |
| `VITE_OPEN_BROWSER` | `true` (set `false` to stay closed) |

## Routes

| Path | Page |
|---|---|
| `/` | Home: action cards and a preview of the active collection |
| `/chat/:sessionId` | A chat session |
| `/collection/:collectionId` | Every video, audio and image in a collection |
| `/collection/:collectionId/video/:videoId` | One video; messages sent here are about that video |
| `/setup` | Shown until `/config/check` reports a complete setup |

Sending a message from any page other than a chat starts a new session and opens it.

## Layout

```
src/
  main.ts, App.vue
  router/          routes + the setup guard
  layouts/         AppLayout: sidebar, header, composer, dialogs (stays mounted)
  pages/           one component per route
  stores/          Pinia: chat, sessions, collections, config, ui
  api/             typed fetch wrappers per backend area
  composables/     useChatSocket (one /chat socket), useChatActions (send + navigate), useOpenVideo
  components/      UI components and message handlers
  messageRenderers.ts   content.type → component
  types/           backend shapes (mirrors backend/director/core/session.py)
  config.ts        backend URL, sidebar links, demo videos
```

## Message handlers

Each `content` item in an assistant message is rendered by the component registered for its `type` in `src/messageRenderers.ts`:

| `type` | Component |
|---|---|
| `text` | `TextResponse` |
| `video` | `ChatVideo` |
| `videos` | `ChatVideos` |
| `image` | `ImageHandler` |
| `search_results` | `ChatSearchResults` |

When a new `ContentType` is added to the backend, add a component under `src/components/message-handlers/` and register it there. Unknown types are skipped.
