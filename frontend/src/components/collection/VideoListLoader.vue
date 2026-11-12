<template>
  <div class="vdb-c-grid vdb-c-grid-cols-12 vdb-c-gap-24 sm:vdb-c-gap-32">
    <div
      v-for="(item, index) in [1, 2, 3, 4]"
      :key="`post-loading-${index}`"
      class="vdb-c-col-span-12 sm:vdb-c-col-span-6 md:vdb-c-col-span-4 lg:vdb-c-col-span-3"
    >
      <video-card-loader :index="index" />
    </div>
  </div>
</template>

<script>

import VideoCardLoader from './VideoCardLoader.vue'
export default {
  name: 'AllVideoLoader',
  components:{
    VideoCardLoader,
  }
}
</script>
