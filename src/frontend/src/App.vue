<template>
  <div class="min-h-screen bg-surface">
    <TopNavigation />
    <main class="pt-16">
      <router-view />
    </main>
    <BottomNavBar v-if="showBottomNav" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TopNavigation from '@/components/TopNavigation.vue'
import BottomNavBar from '@/components/BottomNavBar.vue'

const route = useRoute()

const showBottomNav = computed(() => {
  const hiddenOnExact = ['/']
  if (hiddenOnExact.includes(route.path)) return false
  const hiddenOnPrefix = ['/settings', '/characters', '/projects']
  return !hiddenOnPrefix.some(r => route.path.startsWith(r))
})
</script>
