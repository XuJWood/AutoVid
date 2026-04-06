<template>
  <div class="min-h-screen bg-surface">
    <TopNavBar />
    <main class="pt-16">
      <router-view />
    </main>
    <BottomNavBar v-if="showBottomNav" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TopNavBar from '@/components/TopNavBar.vue'
import BottomNavBar from '@/components/BottomNavBar.vue'

const route = useRoute()

const showBottomNav = computed(() => {
  const hiddenRoutes = ['settings', 'model-config']
  return !hiddenRoutes.some(r => route.name?.includes(r))
})
</script>
