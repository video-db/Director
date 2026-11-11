<template>
  <div class="vdb-c-relative vdb-c-rounded-20 vdb-c-bg-white">
    <LoadingMessage
      :status="content.status"
      :message="content.status_message"
      :is-last-conv="isLastConv"
    />
    <div v-if="content.status === 'success'">
      <search-list-item
        :search-results="content.search_results"
        :is-contractable="content.search_results.length > 1"
      />
    </div>
    <div v-else-if="content.status === 'progress'">
      <search-list-item-loader />
    </div>
  </div>
</template>

<script setup>
import SearchListItem from "./search/SearchListItem.vue";
import LoadingMessage from "./elements/LoadingMessage.vue";
import SearchListItemLoader from "./search/SearchListItemLoader.vue";

const props = defineProps({
  content: {
    type: Object,
    required: true,
  },
  isLastConv: {
    type: Boolean,
    default: false,
  },
});
const getArr = () => {
  const arr = [];
  for (let i = 0; i < 2; i++) {
    arr.push(i + 1);
  }
  return arr;
};
</script>

<style></style>
