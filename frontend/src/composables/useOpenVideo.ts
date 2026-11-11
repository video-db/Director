import { useRouter } from "vue-router";

import type { Video } from "@/types";

// Demo cards link out; collection videos open their page.
export function useOpenVideo() {
  const router = useRouter();
  return (video: Video) => {
    if (video.external_url) {
      window.open(video.external_url, "_blank");
      return;
    }
    router.push({
      name: "video",
      params: { collectionId: video.collection_id, videoId: video.id },
    });
  };
}
