<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-7xl mx-auto">
    <!-- Hero Section -->
    <div class="text-center mb-16">
      <h1 class="text-4xl font-extrabold tracking-tight font-headline text-on-background mb-4">
        欢迎使用 AutoVid
      </h1>
      <p class="text-lg text-on-surface-variant">
        AI短剧创作平台，从创意到成片一站式完成
      </p>
    </div>

    <!-- Entry Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-16">
      <!-- Short Drama Entry -->
      <router-link
        to="/drama/create"
        class="group bg-surface-container-lowest p-8 rounded-lg shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all border border-primary/5"
      >
        <div class="flex items-center gap-4 mb-6">
          <div class="p-3 bg-primary/10 rounded-lg">
            <span class="material-symbols-outlined text-primary text-3xl">movie</span>
          </div>
          <h2 class="text-xl font-bold font-headline">短剧创作</h2>
        </div>
        <p class="text-on-surface-variant mb-4">
          文字 → 剧本 → 角色 → 分镜 → 完整短剧
        </p>
        <p class="text-sm text-on-surface-variant/70 mb-6">
          适用于：连续剧、系列内容
        </p>
        <div class="flex items-center gap-2 text-primary font-bold text-sm group-hover:gap-4 transition-all">
          <span>开始创作</span>
          <span class="material-symbols-outlined text-lg">arrow_forward</span>
        </div>
      </router-link>

      <!-- Video Generation Entry -->
      <router-link
        to="/video/select"
        class="group bg-surface-container-lowest p-8 rounded-lg shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all border border-primary/5"
      >
        <div class="flex items-center gap-4 mb-6">
          <div class="p-3 bg-tertiary/10 rounded-lg">
            <span class="material-symbols-outlined text-tertiary text-3xl">videocam</span>
          </div>
          <h2 class="text-xl font-bold font-headline">视频生成</h2>
        </div>
        <p class="text-on-surface-variant mb-4">
          人物 → 场景 → 视频，保持角色一致性
        </p>
        <p class="text-sm text-on-surface-variant/70 mb-6">
          适用于：单条视频、角色IP打造
        </p>
        <div class="flex items-center gap-2 text-tertiary font-bold text-sm group-hover:gap-4 transition-all">
          <span>开始生成</span>
          <span class="material-symbols-outlined text-lg">arrow_forward</span>
        </div>
      </router-link>
    </div>

    <!-- Recent Projects -->
    <div v-if="loading" class="text-center py-8">
      <span class="material-symbols-outlined text-3xl text-primary animate-spin">autorenew</span>
    </div>
    <div v-else-if="error" class="bg-yellow-50 text-yellow-800 rounded-lg p-4 text-center text-sm">
      {{ error }}
    </div>
    <div v-else-if="recentProjects.length > 0">
      <h3 class="text-lg font-bold font-headline mb-6">近期项目</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <router-link
          v-for="project in recentProjects"
          :key="project.id"
          :to="project.type === 'drama' ? `/drama/${project.id}` : `/video/result`"
          class="bg-surface-container-lowest rounded-lg overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all"
        >
          <div class="aspect-video bg-surface-container">
            <img
              v-if="covers[project.id]"
              :src="covers[project.id]"
              class="w-full h-full object-cover"
              @error="(e) => e.target.style.display = 'none'"
            />
            <div v-if="!covers[project.id]" class="w-full h-full flex items-center justify-center">
              <span class="material-symbols-outlined text-4xl text-on-surface-variant opacity-30">movie</span>
            </div>
          </div>
          <div class="p-4">
            <h4 class="font-bold text-sm mb-1">{{ project.name }}</h4>
            <p class="text-xs text-on-surface-variant">{{ formatDate(project.updated_at || project.created_at) }}</p>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projectsApi } from '@/api/projects'
import { storyboardApi } from '@/api/storyboard'

const recentProjects = ref([])
const loading = ref(true)
const error = ref('')
const covers = ref({})

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const response = await projectsApi.getAll()
    recentProjects.value = response.data.slice(0, 6)
    // Load cover images from first episode
    const coverResults = await Promise.allSettled(
      recentProjects.value.map(p =>
        storyboardApi.getByProject(p.id)
          .then(r => {
            const eps = (r.data || []).sort((a, b) => (a.episode_number || 0) - (b.episode_number || 0))
            const withCover = eps.find(e => e.image_url)
            if (withCover) covers.value[p.id] = toPlayableUrl(withCover.image_url)
          })
          .catch(() => {})
      )
    )
  } catch (e) {
    console.error('Failed to load projects:', e)
    error.value = '加载项目失败，请检查后端服务是否运行'
  } finally {
    loading.value = false
  }
})
</script>
