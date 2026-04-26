<template>
  <div class="fixed bottom-8 w-full flex justify-center z-50">
    <nav class="rounded-full px-6 py-3 bg-white/80 backdrop-blur-2xl border border-on-surface-variant/10 shadow-lg shadow-primary/10 flex justify-around items-center gap-4">
      <button
        v-if="showBack"
        @click="$router.back()"
        class="text-on-surface-variant px-4 py-2 flex items-center gap-2 hover:bg-surface-container-low transition-all rounded-full font-bold text-xs"
      >
        <span class="material-symbols-outlined">arrow_back</span>
        <span>返回</span>
      </button>
      <button
        v-if="nextRoute"
        @click="$router.push(nextRoute)"
        class="bg-primary text-white rounded-full px-6 py-2 flex items-center gap-2 scale-105 active:scale-95 duration-300 font-bold text-xs shadow-lg shadow-primary/30"
      >
        <span>{{ nextLabel }}</span>
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const projectId = computed(() => route.params.id)

const showBack = computed(() => {
  return route.path !== '/drama/create'
})

const nextRoute = computed(() => {
  const p = route.path
  if (p === '/drama/create') return null
  if (p.startsWith('/video/select')) return '/video/scene'
  if (p.startsWith('/video/scene')) return '/video/result'
  if (!projectId.value) return null
  if (p.endsWith(`/drama/${projectId.value}`)) return `/drama/${projectId.value}/storyboard`
  if (p.endsWith('/storyboard')) return `/drama/${projectId.value}/preview`
  return null
})

const nextLabel = computed(() => {
  const p = route.path
  if (p.endsWith(`/drama/${projectId.value}`)) return '编辑剧集'
  if (p.endsWith('/storyboard')) return '预览剧集'
  if (p.startsWith('/video/select')) return '配置场景'
  if (p.startsWith('/video/scene')) return '查看结果'
  return '下一步'
})
</script>
