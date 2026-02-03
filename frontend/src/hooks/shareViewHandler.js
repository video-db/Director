import { computed, onBeforeMount, reactive, ref, toRefs, watch } from "vue";

const fetchData = async (rootUrl, endpoint) => {
  const res = {};
  res.status = "success";
  res.data = {};
  return res;
};

export function publicUseVideoDBAgent(config, sessionId) {
  const { debug = false, socketUrl, httpUrl } = config;
  if (debug) console.log("debug :videodb-chat config", config);

  const session = reactive({
    isConnected: true,
    sessionId,
    videoId: null,
    collectionId: "default",
  });

  const configStatus = ref(null);

  const collections = ref([]);
  const sessions = ref([]);
  const sessionsSorted = computed(() => {
    return [...sessions.value].sort((a, b) => b.created_at - a.created_at);
  });
  const agents = ref([]);

  const conversations = reactive({});
  const activeCollectionData = ref(null);

  const activeCollectionVideos = ref(null);
  const activeVideoData = ref(null);

  const activeCollectionAudios = ref(null);
  const activeAudioData = ref(null);

  const activeCollectionImages = ref(null);
  const activeImageData = ref(null);

  fetch(`${httpUrl}/session/public/${sessionId}`)
    .then((res) => res.json())
    .then((res) => {
      console.log("debug :videodb-chat res", res);
      if (res) {
        session.videoId = res.video_id || null;
        session.collectionId =
          res.collection_id || session.collectionId || null;

        // Clear existing conversations
        Object.keys(conversations).forEach((key) => delete conversations[key]);

        // Populate conversations with fetched data
        if (res.conversation) {
          res.conversation.forEach((message) => {
            const { conv_id, msg_id } = message;
            if (!conversations[conv_id]) {
              conversations[conv_id] = {};
            }
            conversations[String(conv_id)][String(msg_id)] = {
              sender: message.msg_type === "input" ? "user" : "assistant",
              ...message,
            };
          });
        }
      }
    })
    .catch((error) => {
      if (debug) console.error("Error fetching public session:", error);
    });
  const fetchConfigStatus = async () => {
    try {
      const res = await fetchData(httpUrl, "/config/check");
      return res;
    } catch (error) {
      if (debug) console.error("Error fetching config status:", error);
      return { data: { backend: false } };
    }
  };

  const uploadMedia = async (uploadData) => {};

  const generateAudioUrl = async (collectionId, audioId) => {
    const res = {};
    res.status = "success";
    res.url = "";
    return res;
  };

  const generateImageUrl = async (collectionId, imageId) => {
    const res = {};
    res.status = "success";
    res.url = "";
    return res;
  };

  const saveMeetingContext = async (msgId, context) => {
    const res = {};
    res.status = "success";
    res.data = {};
    return res;
  };

  const makeSessionPublic = async (sessionId, isPublic = true) => {
    const res = {};
    res.status = "success";
    res.data = {};
    return res;
  };

  const fetchMeetingContext = async (uiId) => {
    const res = {};
    res.status = "success";
    res.data = {};
    return res;
  };

  const refetchCollectionVideos = async () => {};

  const refetchCollectionAudios = async () => {};

  const refetchCollectionImages = async () => {};

  onBeforeMount(() => {
    fetchConfigStatus().then((res) => {
      if (debug) console.log("debug :videodb-chat config status", res);
      configStatus.value = res.data;
    });
  });

  const loadSession = (sessionId) => {};

  const deleteSession = (sessionId) => {};

  const updateCollection = async () => {};

  const createCollection = async (name, description) => {};

  const deleteCollection = async (collectionId) => {};

  const deleteVideo = async (collectionId, videoId) => {};

  const deleteAudio = async (collectionId, audioId) => {};

  const deleteImage = async (collectionId, imageId) => {};

  const addMessage = (message) => {};

  return {
    ...toRefs(session),
    configStatus,
    collections,
    sessions: sessionsSorted,
    agents,
    activeCollectionData,
    activeCollectionVideos,
    activeVideoData,
    refetchCollectionVideos,
    activeCollectionAudios,
    activeAudioData,
    refetchCollectionAudios,
    activeCollectionImages,
    activeImageData,
    refetchCollectionImages,
    conversations,
    addMessage,
    loadSession,
    deleteSession,
    updateCollection,
    createCollection,
    deleteCollection,
    deleteVideo,
    deleteAudio,
    deleteImage,
    uploadMedia,
    generateImageUrl,
    generateAudioUrl,
    saveMeetingContext,
    fetchMeetingContext,
    makeSessionPublic,
  };
}
