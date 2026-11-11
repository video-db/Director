import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  listCollections: vi.fn(),
  listVideos: vi.fn(),
  listAudios: vi.fn(),
  listImages: vi.fn(),
  deleteMedia: vi.fn(),
}));
vi.mock("@/api/collections", () => api);

import { useCollectionsStore } from "../collections";

describe("collections store", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
    api.listCollections.mockResolvedValue([
      { id: "c-default", name: "default" },
      { id: "c-2", name: "Second" },
    ]);
    api.listVideos.mockResolvedValue([
      { id: "v1", collection_id: "c-default", name: "One" },
      { id: "v2", collection_id: "c-default", name: "Two" },
    ]);
    api.listAudios.mockResolvedValue([]);
    api.listImages.mockResolvedValue([]);
  });

  it("names the default collection and makes it active", async () => {
    const store = useCollectionsStore();
    await store.load();
    expect(store.collections[0].name).toBe("VideoDB Default Collection");
    expect(store.activeCollectionId).toBe("c-default");
    expect(store.videos).toHaveLength(2);
    expect(store.isContentLoading).toBe(false);
    expect(localStorage.getItem("videodb-chat:active-collection")).toBe(
      "c-default",
    );
  });

  it("drops a deleted video from the active collection", async () => {
    api.deleteMedia.mockResolvedValue({ success: true });
    const store = useCollectionsStore();
    await store.load();
    await store.deleteMedia("video", { id: "v1", collection_id: "c-default" });
    expect(store.videos?.map((v) => v.id)).toEqual(["v2"]);
  });

  it("surfaces a failed delete", async () => {
    api.deleteMedia.mockResolvedValue({ success: false, message: "nope" });
    const store = useCollectionsStore();
    await store.load();
    await expect(
      store.deleteMedia("video", { id: "v1", collection_id: "c-default" }),
    ).rejects.toThrow("nope");
    expect(store.videos).toHaveLength(2);
  });
});
