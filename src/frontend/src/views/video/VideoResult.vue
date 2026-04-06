<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-4xl mx-auto">
    <div class="text-center mb-8">
      <span class="material-symbols-outlined text-6xl text-primary mb-4">check_circle</span>
      <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">
        视频生成完成
      </h1>
      <p class="text-on-surface-variant">您的视频已成功生成</p>
    </div>

    <!-- Video Preview -->
    <div class="bg-surface-container-lowest rounded-lg overflow-hidden shadow-lg mb-8">
      <div class="aspect-video bg-black flex items-center justify-center">
        <div v-if="video?.file_path" class="w-full h-full">
          <video :src="video.file_path" controls class="w-full h-full"></video>
        </div>
        <div v-else class="text-white/50 text-center">
          <span class="material-symbols-outlined text-6xl mb-4">movie</span>
          <p>视频预览</p>
        </div>
      </div>
      <div class="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p class="text-xs text-on-surface-variant">分辨率</p>
          <p class="font-bold">{{ video?.resolution || '1080p' }}</p>
        </div>
        <div>
          <p class="text-xs text-on-surface-variant">时长</p>
          <p class="font-bold">{{ video?.duration || 5 }}秒</p>
        </div>
        <div>
          <p class="text-xs text-on-surface-variant">生成模型</p>
          <p class="font-bold">{{ video?.model_provider || 'Cinematic v3' }}</p>
        </div>
        <div>
          <p class="text-xs text-on-surface-variant">生成时间</p>
          <p class="font-bold">{{ formatDate(video?.created_at) }}</p>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-center gap-4 flex-wrap">
      <button class="px-6 py-3 bg-surface-container text-on-surface font-bold rounded-full text-sm hover:bg-surface-container-high transition-colors flex items-center gap-2">
        <span class="material-symbols-outlined">refresh</span>
        重新生成
      </button>
      <button class="px-6 py-3 bg-surface-container text-on-surface font-bold rounded-full text-sm hover:bg-surface-container-high transition-colors flex items-center gap-2">
        <span class="material-symbols-outlined">edit</span>
        编辑视频
      </button>
      <button class="px-6 py-3 bg-surface-container text-on-surface font-bold rounded-full text-sm hover:bg-surface-container-high transition-colors flex items-center gap-2">
        <span class="material-symbols-outlined">download</span>
        下载视频
      </button>
      <button class="px-6 py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors flex items-center gap-2">
        <span class="material-symbols-outlined">share</span>
        发布视频
      </button>
    </div>

    <!-- Publish Section -->
    <div class="mt-12 bg-surface-container-lowest rounded-lg p-8">
      <h2 class="text-lg font-bold mb-6">发布到平台</h2>
      <div class="mb-6">
        <label class="text-sm font-bold text-on-surface-variant mb-2 block">视频标题</label>
        <input
          v-model="publishTitle"
          type="text"
          class="w-full bg-surface-container-low border-none rounded-lg p-4"
          placeholder="输入视频标题..."
        />
      </div>
      <div class="mb-6">
        <label class="text-sm font-bold text-on-surface-variant mb-3 block">选择平台</label>
        <div class="flex gap-3 flex-wrap">
          <button
            v-for="platform in platforms"
            :key="platform.id"
            @click="togglePlatform(platform.id)"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-bold transition-colors border',
              selectedPlatforms.includes(platform.id)
                ? 'bg-primary/10 border-primary text-primary'
                : 'bg-surface-container-low border-transparent text-on-surface-variant hover:bg-surface-container'
            ]"
          >
            {{ platform.name }}
          </button>
        </div>
      </div>
      <button
        :disabled="selectedPlatforms.length === 0"
        class="w-full py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors disabled:opacity-50"
      >
        一键发布
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { videosApi } from '@/api/videos'

const route = useRoute()
const video = ref(null)
const publishTitle = ref('')
const selectedPlatforms = ref([])

const platforms = [
  { id: 'douyin', name: '抖音' },
  { id: 'kuaishou', name: '快手' },
  { id: 'xiaohongshu', name: '小红书' },
  { id: 'bilibili', name: 'B站' },
  { id: 'wechat', name: '视频号' }
]

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const togglePlatform = (platformId) => {
  const index = selectedPlatforms.value.indexOf(platformId)
  if (index > -1) {
    selectedPlatforms.value.splice(index, 1)
  } else {
    selectedPlatforms.value.push(platformId)
  }
}

onMounted(async () => {
  // Load video if we have an ID
  const videoId = route.query.id
  if (videoId) {
    try {
      const response = await videosApi.get(videoId)
      video.value = response.data
    } catch (error) {
      console.error('Failed to load video:', error)
    }
  }
})
</script>
