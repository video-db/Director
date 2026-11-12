<template>
  <div class="vdb-c-border-t vdb-c-border-kilvish-400 vdb-c-p-16">
    <div
      :class="[
        'vdb-c-relative vdb-c-border vdb-c-p-8',
        inputFocused ? 'vdb-c-border-kilvish-600' : 'vdb-c-border-kilvish-400',
        isExpanded ? 'vdb-c-rounded-20' : 'vdb-c-rounded-[50px]',
      ]"
    >
      <div
        class="vdb-c-m-8 vdb-c-mb-14 vdb-c-flex vdb-c-flex-col vdb-c-gap-8"
        v-if="imageAttachments.length > 0"
      >
        <ChatInputImagePreview
          v-for="attachment in imageAttachments"
          :key="attachment.key"
          :attachment="attachment"
          @remove="removeAttachment(attachment)"
        />
      </div>

      <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-8">
        <!-- Upload Button -->
        <div
          :class="[
            'vdb-c-chat-input-upload-icon vdb-c-ml-4 vdb-c-cursor-pointer vdb-c-px-8',
            isExpanded ? 'vdb-c-self-end vdb-c-py-10' : 'vdb-c-py-2',
          ]"
        >
          <label class="vdb-c-cursor-pointer">
            <input
              id="upload"
              type="file"
              accept="image/*"
              class="vdb-c-hidden"
              @change="handleFileUpload"
            />
            <PaperClipIcon />
          </label>
        </div>

        <!-- Textarea -->
        <textarea
          ref="inputRef"
          type="text"
          class="vdb-c-chat-input vdb-c-max-h-[25vh] vdb-c-font-medium vdb-c-text-[#1D2736] vdb-c-placeholder-kilvish-500 vdb-c-outline-none focus:vdb-c-outline-none"
          rows="1"
          :placeholder="placeholder"
          autocomplete="off"
          :value="chatInput"
          @input="handleInput"
          @focus="inputFocused = true"
          @blur="handleBlur"
          @keydown="handleKeyDown"
          @paste="handlePaste"
        ></textarea>

        <!-- Send Button -->
        <div
          class="vdb-c-flex vdb-c-items-center"
          :class="{
            'vdb-c-self-end': isExpanded,
          }"
        >
          <button
            :disabled="isInputDisabled"
            class="vdb-c-font-sans vdb-c-hidden vdb-c-h-40 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-px-12 vdb-c-py-8 vdb-c-text-sm vdb-c-font-bold vdb-c-uppercase vdb-c-text-white vdb-c-transition md:vdb-c-flex"
            :class="{
              'vdb-c-cursor-not-allowed vdb-c-bg-kilvish-400 hover:vdb-c-bg-kilvish-400':
                isInputDisabled,
              'hover:vdb-c-orange-400 vdb-c-cursor-pointer vdb-c-bg-orange':
                !isInputDisabled,
            }"
            @click="handleSubmit"
            type="submit"
          >
            <EllipsesLoading v-if="chatLoading" />
            <div v-else class="vdb-c-flex vdb-c-items-center vdb-c-pl-4">
              <span class="vdb-c-inline">Send</span>
              <chat-enter-icon class-name="vdb-c-ml-4" />
            </div>
          </button>
          <button
            class="vdb-c-mobile-send vdb-c-flex vdb-c-border-none vdb-c-bg-transparent vdb-c-p-8 vdb-c-pr-12 md:vdb-c-hidden"
            :class="{
              'vdb-c-bg-kilvish-400 vdb-c-text-kilvish-400': isInputDisabled,
              'vdb-c-mobile-send vdb-c-text-others-nightwing': !isInputDisabled,
            }"
            @click="handleSubmit"
            type="submit"
          >
            <send-icon class-name="vdb-c-w-24 vdb-c-h-24" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { v4 as uuidv4 } from "uuid";
import { computed, nextTick, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "@/stores/chat";
import ChatEnterIcon from "../icons/ChatEnter.vue";
import PaperClipIcon from "../icons/PaperClip.vue";
import SendIcon from "../icons/Send.vue";
import ChatInputImagePreview from "./elements/ChatInputImagePreview.vue";
import EllipsesLoading from "./elements/EllipsesLoading.vue";

const props = defineProps({
  placeholder: {
    type: String,
    default: "Ask a question",
  },
  contextData: {
    type: Object,
    default: null,
  },
});

const chat = useChatStore();
const { chatInput, chatLoading } = storeToRefs(chat);
// Reactive array; mutated in place, never reassigned.
const chatAttachments = chat.chatAttachments;

const emit = defineEmits(["on-submit", "on-change"]);

const charCount = ref(0);
const inputFocused = ref(false);
const inputRef = ref(null);
const isTextBoxExpanded = ref(false);

const focus = () => {
  inputRef.value.focus();
};

const imageAttachments = computed(() =>
  chatAttachments.filter((attachment) => attachment.type === "image"),
);

const isInputDisabled = computed(() => {
  const hasUploadingImages = imageAttachments.value.some(
    (attachment) =>
      attachment.upload_status === "uploading" ||
      attachment.upload_status === "in_queue",
  );
  return chatLoading.value || charCount.value < 1 || hasUploadingImages;
});

const isExpanded = computed(
  () => isTextBoxExpanded.value || chatAttachments.length > 0,
);

const handleInput = (e) => {
  const newValue = e.target.value;
  chatInput.value = newValue;
  adjustHeight(); // Adjust height dynamically
};

const handleBlur = () => {
  inputFocused.value = false;
};

const handleKeyDown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    if (chatInput.value.trim() !== "") {
      handleSubmit(e);
    } else {
      e.preventDefault();
    }
  } else if (e.shiftKey && e.key === "Enter") {
    adjustHeight(); // Adjust height on Shift+Enter
    return;
  }
};

watch(
  chatInput,
  (newValue) => {
    charCount.value = newValue.length;
  },
  { immediate: true },
);

const handlePaste = (event) => {
  const clipboardData = event.clipboardData || window.clipboardData;
  const items = Array.from(clipboardData.items);

  const imageItem = items.find(
    (item) => item.kind === "file" && item.type.startsWith("image/"),
  );

  if (imageItem) {
    const file = imageItem.getAsFile();
    if (file) {
      const newImageAttachment = {
        type: "image",
        image_data: file,
        key: uuidv4(),
        upload: true,
        upload_status: "in_queue",
      };
      attachAttachment(newImageAttachment);
    }
    event.preventDefault(); // Prevent default paste behavior
  }
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    const newImageAttachment = {
      type: "image",
      image_data: file,
      key: uuidv4(),
      upload: true,
      upload_status: "in_queue",
    };
    attachAttachment(newImageAttachment);
  }
};

const handleSubmit = async (e) => {
  if (isInputDisabled.value) return;
  e.preventDefault();
  if (chatInput.value.trim() !== "") {
    emit("on-submit", {
      text: chatInput.value,
      images: imageAttachments.value,
    });
    chatInput.value = "";
    clearAllAttachments();
    charCount.value = 0;
    await nextTick();
    adjustHeight();
  }
};

function adjustHeight() {
  const textarea = inputRef.value;
  textarea.style.height = "auto"; // Reset height to recalculate
  textarea.style.height = textarea.scrollHeight + "px"; // Set height based on content
  if (textarea.scrollHeight > 30) {
    isTextBoxExpanded.value = true;
  } else {
    isTextBoxExpanded.value = false;
  }
}

const attachAttachment = (attachment) => {
  chatAttachments[0] = attachment;
};

const removeAttachment = (attachment) => {
  const index = chatAttachments.findIndex(
    (item) => item.key === attachment.key,
  );
  if (index !== -1) {
    chatAttachments.splice(index, 1);
  }
};

const clearAllAttachments = () => {
  chatAttachments.splice(0, chatAttachments.length);
};

defineExpose({
  focus,
});
</script>

<style>
/* Shared Styling */
.vdb-c-br-50 {
  border-radius: 50px;
}

/* Chat Input */
.vdb-c-chat-input {
  flex-grow: 1;
  resize: none;
}

.vdb-c-chat-input::placeholder {
  font-weight: 400;
}
</style>
