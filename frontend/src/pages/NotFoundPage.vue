<template>
  <div
    class="vdb-c-flex vdb-c-w-full vdb-c-flex-1 vdb-c-flex-col vdb-c-items-center vdb-c-justify-center vdb-c-gap-16 vdb-c-text-center"
  >
    <p class="vdb-c-text-xl vdb-c-font-semibold vdb-c-text-kilvish-900">
      Page not found
    </p>
    <RouterLink :to="{ name: 'home' }">
      <Button variant="secondary">Back to home</Button>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import Button from "@/components/buttons/Button.vue";
</script>
