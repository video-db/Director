// Collections, the active collection's media, and the video in focus.
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as api from "@/api/collections";
import type { Audio, Collection, Image, MediaKind, Video } from "@/types";

const ACTIVE_KEY = "videodb-chat:active-collection";
const DEFAULT_NAME = "VideoDB Default Collection";

export const useCollectionsStore = defineStore("collections", () => {
  const collections = ref<Collection[]>([]);
  const loaded = ref(false);
  const activeCollectionId = ref<string | null>(
    localStorage.getItem(ACTIVE_KEY),
  );
  // Set when the active id isn't in the list (e.g. a deep link).
  const fetchedCollection = ref<Collection | null>(null);

  // null = not loaded yet.
  const videos = ref<Video[] | null>(null);
  const audios = ref<Audio[] | null>(null);
  const images = ref<Image[] | null>(null);
  const activeVideo = ref<Video | null>(null);

  const activeCollection = computed(
    () =>
      collections.value.find((c) => c.id === activeCollectionId.value) ??
      fetchedCollection.value,
  );

  const isContentLoading = computed(
    () => !(videos.value && audios.value && images.value),
  );

  const isEmpty = computed(
    () =>
      !isContentLoading.value &&
      videos.value!.length + audios.value!.length + images.value!.length === 0,
  );

  const isFreshUser = computed(
    () => loaded.value && collections.value.length < 2 && isEmpty.value,
  );

  async function load() {
    const list = await api.listCollections();
    // The backend lists the default collection first.
    if (list[0]) list[0] = { ...list[0], name: DEFAULT_NAME };
    collections.value = list;
    loaded.value = true;
    const current = activeCollectionId.value;
    if (!current || !list.some((c) => c.id === current)) {
      if (list[0]) await setActive(list[0].id);
    } else if (videos.value === null) {
      await setActive(current, true);
    }
  }

  async function setActive(id: string, force = false) {
    if (id === activeCollectionId.value && !force && videos.value !== null) {
      return;
    }
    activeCollectionId.value = id;
    localStorage.setItem(ACTIVE_KEY, id);
    videos.value = audios.value = images.value = null;
    fetchedCollection.value = null;
    if (loaded.value && !collections.value.some((c) => c.id === id)) {
      api.getCollection(id).then((c) => {
        if (activeCollectionId.value === id) fetchedCollection.value = c;
      });
    }
    await Promise.all([refetch("video"), refetch("audio"), refetch("image")]);
  }

  async function refetch(kind: MediaKind) {
    const id = activeCollectionId.value;
    if (!id) return;
    const isCurrent = () => activeCollectionId.value === id;
    try {
      if (kind === "video") {
        const list = await api.listVideos(id);
        if (isCurrent()) videos.value = list;
      } else if (kind === "audio") {
        const list = await api.listAudios(id);
        if (isCurrent()) audios.value = list;
      } else {
        const list = await api.listImages(id);
        if (isCurrent()) images.value = list;
      }
    } catch {
      // Show the empty state rather than an endless loader.
      if (!isCurrent()) return;
      if (kind === "video") videos.value ??= [];
      else if (kind === "audio") audios.value ??= [];
      else images.value ??= [];
    }
  }

  function refetchAll() {
    return Promise.all([refetch("video"), refetch("audio"), refetch("image")]);
  }

  async function focusVideo(collectionId: string, videoId: string | null) {
    activeVideo.value = null;
    if (!videoId) return;
    const video = await api.getVideo(collectionId, videoId);
    if (activeCollectionId.value === collectionId) activeVideo.value = video;
  }

  async function create(name: string, description: string) {
    const collection = await api.createCollection(name, description);
    await load();
    return collection;
  }

  async function remove(id: string) {
    const res = await api.deleteCollection(id);
    if (!res.success) throw new Error(res.message || "Failed to delete");
    collections.value = collections.value.filter((c) => c.id !== id);
    await load();
  }

  async function deleteMedia(
    kind: MediaKind,
    media: { id: string; collection_id: string },
  ) {
    const res = await api.deleteMedia(kind, media.collection_id, media.id);
    if (!res.success)
      throw new Error(res.message || `Failed to delete ${kind}`);
    if (media.collection_id !== activeCollectionId.value) return;
    const drop = <T extends { id: string }>(list: T[] | null) =>
      list?.filter((m) => m.id !== media.id) ?? null;
    if (kind === "video") videos.value = drop(videos.value);
    else if (kind === "audio") audios.value = drop(audios.value);
    else images.value = drop(images.value);
  }

  // Cards expect { status, url }.
  const mediaUrl =
    (kind: "audio" | "image") => async (collectionId: string, id: string) => {
      try {
        const url = await api.generateMediaUrl(kind, collectionId, id);
        return { status: "success", url };
      } catch (error) {
        return { status: "error", error };
      }
    };

  return {
    collections,
    loaded,
    activeCollectionId,
    activeCollection,
    videos,
    audios,
    images,
    activeVideo,
    isContentLoading,
    isEmpty,
    isFreshUser,
    load,
    setActive,
    refetch,
    refetchAll,
    focusVideo,
    create,
    remove,
    deleteMedia,
    generateImageUrl: mediaUrl("image"),
    generateAudioUrl: mediaUrl("audio"),
  };
});
