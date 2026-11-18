export const backendUrl: string =
  import.meta.env.VITE_APP_BACKEND_URL || "http://127.0.0.1:8000";
export const socketUrl = `${backendUrl}/chat`;

// Material Symbols names.
export const sidebarLinks = [
  {
    href: "https://www.youtube.com/playlist?list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw",
    text: "Watch demos",
    icon: "play_circle",
  },
  { href: "https://console.videodb.io", text: "VideoDB Console", icon: "open_in_new" },
];

export const chatInputPlaceholder = "Ask Director";

export const demoVideos = [
  {
    id: "demo-1",
    external_url: "https://www.youtube.com/watch?v=Dncn_0RWrro",
    thumbnail_url:
      "https://raw.githubusercontent.com/video-db/videodb-cookbook-assets/main/images/thumbnail_automated.png",
  },
  {
    id: "demo-2",
    external_url: "https://www.youtube.com/watch?v=bct8Vvl2acU",
    thumbnail_url:
      "https://raw.githubusercontent.com/video-db/videodb-cookbook-assets/main/images/thumbnail_gen_ai.png",
  },
  {
    id: "demo-3",
    external_url: "https://www.youtube.com/watch?v=KcoA0eio1Zo",
    thumbnail_url:
      "https://raw.githubusercontent.com/video-db/videodb-cookbook-assets/main/images/thumbnail_profanity.png",
  },
  {
    id: "demo-4",
    external_url: "https://www.youtube.com/watch?v=7J7oBIv4eOY",
    thumbnail_url:
      "https://raw.githubusercontent.com/video-db/videodb-cookbook-assets/main/images/thumbnail_keyword.png",
  },
];
