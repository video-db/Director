<template>
  <div class="vdb-c-flex vdb-c-flex-col vdb-c-h-full">
    <div class="vdb-c-flex sm:vdb-c-block vdb-c-mb-30" :class="{ 'vdb-c-flex-grow': borderB }">
      <div
        class="vdb-c-w-96 vdb-c-min-w-96 sm:vdb-c-w-full sm:vdb-c-min-w-auto vdb-c-mr-24 sm:vdb-c-min-w-0 sm:vdb-c-mb-16"
      >
        <div
          class="vdb-c-relative vdb-c-rounded-12 vdb-c-bg-roy vdb-c-animate-pulse vdb-c-custom-duration"
          style="padding-bottom: 75%"
        />
      </div>
      <div class="vdb-c-flex vdb-c-flex-col vdb-c-justify-center">
        <div class="vdb-c-animate-pulse vdb-c-custom-duration vdb-c-h-20 vdb-c-bg-roy vdb-c-mb-8 vdb-c-rounded-full" />
        <div class="vdb-c-flex vdb-c-items-center">
          <div class="vdb-c-animate-pulse vdb-c-custom-duration vdb-c-w-48 vdb-c-h-20 vdb-c-bg-roy vdb-c-rounded-full vdb-c-mr-12" />
          <div class="vdb-c-animate-pulse vdb-c-custom-duration vdb-c-w-48 vdb-c-h-20 vdb-c-bg-roy vdb-c-rounded-full" />
        </div>
      </div>
    </div>
    <div
      v-if="borderB"
      class="vdb-c-border-b vdb-c-border-outline-xlight lg:vdb-c-mb-16"
      :class="`${index % 2 === 0 ? 'sm:vdb-c--mr-32' : 'sm:vdb-c-mr-0'} ${
        index % 3 !== 2 ? 'md:vdb-c--mr-32' : 'md:vdb-c-mr-0'
      } ${index % 4 !== 3 ? 'lg:vdb-c--mr-32' : 'lg:vdb-c-mr-0'}`"
    />
  </div>
</template>

<script>
export default {
  name: 'VideoCardLoading',
  props: {
    index: {
      type: Number,
      default: 0,
    },
    borderB: {
      type: Boolean,
      default: false,
    },
  },
}
</script>
