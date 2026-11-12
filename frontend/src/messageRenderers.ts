import type { Component } from "vue";

import ChatSearchResults from "@/components/message-handlers/ChatSearchResults.vue";
import ChatVideo from "@/components/message-handlers/ChatVideo.vue";
import ChatVideos from "@/components/message-handlers/ChatVideos.vue";
import ImageHandler from "@/components/message-handlers/ImageHandler.vue";
import TextResponse from "@/components/message-handlers/TextResponse.vue";

// content.type → component. Unknown types are skipped by ChatMessage.
export const messageRenderers: Record<string, Component> = {
  video: ChatVideo,
  videos: ChatVideos,
  text: TextResponse,
  search_results: ChatSearchResults,
  image: ImageHandler,
};
