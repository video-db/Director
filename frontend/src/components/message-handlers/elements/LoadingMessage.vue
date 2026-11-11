<template>
  <div class="vdb-c-flex vdb-c-items-center vdb-c-space-x-2">
    <transition name="fade" mode="out-in">
      <span
        v-if="status === 'progress'"
        class="vdb-c-text-gray-500"
        key="progress"
      >
        <transition name="fade" mode="out-in">
          <span :key="message">{{ message || "Thinking..." }}</span>
        </transition>
      </span>
      <span
        v-else-if="status === 'success'"
        :class="[
          'vdb-c-flex vdb-c-items-center vdb-c-gap-8 vdb-c-font-semibold vdb-c-text-[#333]',
          { 'vdb-c-text-vdb-green': isFocused },
        ]"
        key="success"
      >
        <CheckIcon
          :class="{ bounce: isLastConv }"
          :fill="isFocused ? '#53B745' : '#EC5B16'"
        />
        <span> {{ message || "Here is your response" }} </span>
      </span>
      <span
        v-else-if="status === 'error'"
        :class="[
          'vdb-c-flex vdb-c-items-center vdb-c-gap-8 vdb-c-text-primary',
          {
            'vdb-c-font-semibold': isFocused,
          },
        ]"
        key="error"
      >
        <span> {{ message || "An error occurred" }} </span>
      </span>
      <span v-else-if="status === 'unknown'">
        <Shape1 />
        <span class="vdb-c-font-semibold">
          {{ message || "Here is your response" }}
        </span>
      </span>
    </transition>
  </div>
</template>

<script setup>
import { defineProps, ref, watch } from "vue";

import CheckIcon from "../../icons/Check.vue";
import Shape1 from "../../icons/Shape1.vue";
import RedExclamation from "../../icons/RedExclamation.vue";

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ["progress", "success", "error"].includes(value),
  },
  message: {
    type: String,
  },
  isFocused: {
    type: Boolean,
    default: false,
  },
  isLastConv: {
    type: Boolean,
    default: false,
  },
});

const messageKey = ref(0);

watch(
  () => props.message,
  () => {
    if (props.status === "progress") {
      messageKey.value++;
    }
  },
);
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.bounce {
  display: inline-block;
  animation: bounce-in 0.5s;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.25);
  }
  100% {
    transform: scale(1);
  }
}

.shake {
  display: inline-block;
  animation: shake 0.82s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}

@keyframes shake {
  10%,
  90% {
    transform: translate3d(-1px, 0, 0);
  }

  20%,
  80% {
    transform: translate3d(2px, 0, 0);
  }

  30%,
  50%,
  70% {
    transform: translate3d(-4px, 0, 0);
  }

  40%,
  60% {
    transform: translate3d(4px, 0, 0);
  }
}
</style>
