<template>
  <div
    class="vdb-c-flex vdb-c-flex-col vdb-c-justify-between vdb-c-gap-14 vdb-c-rounded-lg vdb-c-border vdb-c-border-roy vdb-c-px-16 vdb-c-py-16"
    :class="[
      status === 'complete'
        ? ''
        : 'vdb-c-bg-red-200 vdb-c-bg-opacity-20 hover:vdb-c-border-red-200 hover:vdb-c-bg-opacity-100',
    ]"
    style="box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.05)"
  >
    <div class="vdb-c-flex vdb-c-flex-col vdb-c-gap-16">
      <div
        class="vdb-c-flex vdb-c-h-54 vdb-c-w-54 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full"
        :class="[
          status === 'complete' ? 'vdb-c-bg-green-100' : 'vdb-c-bg-red-100',
        ]"
      >
        <QuestionMarkIcon v-if="status === 'incomplete'" fill="#E2462C" />
        <CheckIcon v-else class="vdb-c-h-1/2 vdb-c-w-1/2" />
      </div>
      <div class="vdb-c-flex vdb-c-flex-1 vdb-c-flex-col vdb-c-justify-between">
        <h3 class="vdb-c-font-semibold vdb-c-text-nan">
          {{ title }}
        </h3>
        <p
          :class="[
            'vdb-c-mt-12 vdb-c-text-sm vdb-c-font-medium vdb-c-text-nan',
          ]"
        >
          <span v-if="message.html" v-html="message.html"></span>
          <template v-else>{{ message.text }}</template>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from "vue";
import QuestionMarkIcon from "../../icons/QuestionMark.vue";
import CheckIcon from "../../icons/Check.vue";

defineProps({
  title: String,
  status: {
    type: String,
    validator: (value) => ["incomplete", "complete"].includes(value),
  },
  message: Object,
});
</script>

<style scoped>
a {
  color: #3b82f6;
}
</style>
