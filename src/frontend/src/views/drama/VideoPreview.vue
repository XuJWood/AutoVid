<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold font-headline tracking-tight">视频预览</h1>
          <p class="text-sm text-on-surface-variant mt-1">预览和下载每集视频</p>
        </div>
        <div class="flex gap-3">
          <router-link
            :to="`/drama/${projectId}/storyboard`"
            class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full text-sm font-medium hover:bg-surface-container-high transition-colors"
          >
            <span class="material-symbols-outlined text-sm">arrow_back</span>
            返回剧集编辑
          </router-link>
        </div>
      </div>

      <!-- Stats -->
      <div class="bg-surface-container-low rounded-lg p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600">videocam</span>
              <span class="text-sm"><strong>{{ completedVideos }}</strong> / {{ totalEpisodes }} 集视频已生成</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">schedule</span>
              <span class="text-sm">总时长: <strong>{{ totalDuration }}s</strong></span>
            </div>
          </div>
          <div v-if="progressPercent < 100" class="flex items-center gap-2">
            <div class="w-32 bg-surface-container-high rounded-full h-2">
              <div
                class="bg-primary h-2 rounded-full transition-all"
                :style="{ width: progressPercent + '%' }"
              ></div>
            </div>
            <span class="text-xs text-on-surface-variant">{{ progressPercent }}%</span>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="bg-surface-container-lowest rounded-lg p-12 text-center">
        <span class="material-symbols-outlined text-4xl text-primary animate-spin mb-3">autorenew</span>
        <p class="text-sm text-on-surface-variant">正在加载剧集数据...</p>
      </div>

      <!-- Main Content -->
      <div v-else class="grid grid-cols-12 gap-6">
        <!-- Left: Video Player -->
        <div class="col-span-12 lg:col-span-8">
          <div class="bg-surface-container-lowest rounded-lg overflow-hidden shadow-sm">
            <!-- Main Video -->
            <div class="aspect-video bg-black relative">
              <video
                v-if="currentVideo"
                ref="mainVideo"
                :src="toPlayableUrl(currentVideo.video_url)"
                class="w-full h-full object-contain"
                controls
                @ended="onVideoEnded"
              ></video>
              <div v-else class="w-full h-full flex items-center justify-center">
                <div class="text-center text-white/60">
                  <span class="material-symbols-outlined text-6xl mb-2">play_circle</span>
                  <p class="text-sm">选择一集开始预览</p>
                </div>
              </div>

              <!-- Video Overlay Info -->
              <div v-if="currentVideo" class="absolute bottom-4 left-4 right-4 bg-black/60 text-white px-3 py-2 rounded">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-xs font-bold">第{{ currentVideo.episode_number }}集 · {{ currentVideo.title || '未命名' }}</span>
                  </div>
                  <span class="text-xs font-bold">{{ currentVideo.duration }}s</span>
                </div>
              </div>
            </div>

            <!-- Playback Controls -->
            <div v-if="episodes.length > 0" class="p-4 border-t border-surface-container">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <button
                    @click="playPrevious"
                    :disabled="currentIndex <= 0"
                    class="p-2 rounded-full hover:bg-surface-container transition-colors disabled:opacity-30"
                  >
                    <span class="material-symbols-outlined">skip_previous</span>
                  </button>
                  <button
                    @click="togglePlayAll"
                    class="p-3 bg-primary text-on-primary rounded-full hover:brightness-95 transition-all"
                  >
                    <span class="material-symbols-outlined">{{ isPlayingAll ? 'pause' : 'play_arrow' }}</span>
                  </button>
                  <button
                    @click="playNext"
                    :disabled="currentIndex >= completedEpisodes.length - 1"
                    class="p-2 rounded-full hover:bg-surface-container transition-colors disabled:opacity-30"
                  >
                    <span class="material-symbols-outlined">skip_next</span>
                  </button>
                </div>
                <div class="flex items-center gap-4">
                  <span class="text-sm text-on-surface-variant">{{ currentIndex + 1 }} / {{ completedEpisodes.length }}</span>
                  <span v-if="isPlayingAll" class="text-primary text-sm font-bold">连续播放中</span>
                  <a
                    v-if="currentVideo?.video_url"
                    :href="toPlayableUrl(currentVideo.video_url)"
                    download
                    class="flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-primary/10 text-primary rounded-full hover:bg-primary/20 transition-colors"
                  >
                    <span class="material-symbols-outlined text-sm">download</span>
                    下载本集
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Episode List -->
        <div class="col-span-12 lg:col-span-4">
          <div class="bg-surface-container-lowest rounded-lg shadow-sm">
            <div class="p-4 border-b border-surface-container">
              <h3 class="font-bold text-sm">剧集列表</h3>
            </div>

            <div class="max-h-[600px] overflow-y-auto custom-scrollbar">
              <div v-if="sortedEpisodes.length > 0" class="divide-y divide-surface-container p-4">
                <button
                  v-for="ep in sortedEpisodes"
                  :key="ep.id"
                  @click="selectVideo(ep)"
                  :disabled="!ep.video_url"
                  class="w-full flex items-center gap-3 p-3 rounded-lg transition-colors mb-2"
                  :class="[
                    currentVideo?.id === ep.id ? 'bg-primary/10 border border-primary/30' : 'hover:bg-surface-container-low',
                    !ep.video_url ? 'opacity-50 cursor-not-allowed' : ''
                  ]"
                >
                  <!-- Thumbnail -->
                  <div class="w-20 h-12 bg-surface-container rounded overflow-hidden flex-shrink-0">
                    <img
                      v-if="ep.image_url"
                      :src="toPlayableUrl(ep.image_url)"
                      class="w-full h-full object-cover"
                    />
                    <span v-else class="material-symbols-outlined text-sm text-on-surface-variant flex items-center justify-center h-full">movie</span>
                  </div>

                  <!-- Info -->
                  <div class="flex-1 text-left">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold bg-primary/10 text-primary px-2 py-0.5 rounded">第{{ ep.episode_number }}集</span>
                    </div>
                    <div class="text-sm font-bold mt-0.5">{{ ep.title || '未命名' }}</div>
                    <div class="text-xs text-on-surface-variant">{{ ep.duration }}s</div>
                  </div>

                  <!-- Status -->
                  <div class="flex-shrink-0 text-right">
                    <span v-if="ep.video_url" class="material-symbols-outlined text-sm text-green-600">check_circle</span>
                    <span v-else-if="ep.status === 'processing'" class="material-symbols-outlined text-sm text-yellow-600 animate-spin">sync</span>
                    <span v-else class="material-symbols-outlined text-sm text-on-surface-variant opacity-50">pending</span>
                    <a
                      v-if="ep.video_url"
                      :href="toPlayableUrl(ep.video_url)"
                      download
                      class="block text-xs text-primary mt-1 hover:underline"
                      @click.stop
                    >
                      下载
                    </a>
                  </div>
                </button>
              </div>

              <div v-else class="p-8 text-center text-on-surface-variant">
                <span class="material-symbols-outlined text-4xl opacity-50 mb-2">movie_filter</span>
                <p class="text-sm">还没有剧集数据</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { storyboardApi } from '@/api/storyboard'

const route = useRoute()
const projectId = route.params.id

const episodes = ref([])
const loading = ref(true)
const currentVideo = ref(null)
const currentIndex = ref(0)
const isPlayingAll = ref(false)
const mainVideo = ref(null)

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

const sortedEpisodes = computed(() => {
  return [...episodes.value].sort((a, b) => (a.episode_number || 0) - (b.episode_number || 0))
})

const completedEpisodes = computed(() => {
  return sortedEpisodes.value.filter(e => e.video_url)
})

const totalEpisodes = computed(() => episodes.value.length)
const completedVideos = computed(() => completedEpisodes.value.length)

const totalDuration = computed(() => {
  return episodes.value.reduce((sum, e) => sum + (e.duration || 0), 0)
})

const progressPercent = computed(() => {
  if (totalEpisodes.value === 0) return 0
  return Math.round((completedVideos.value / totalEpisodes.value) * 100)
})

const loadEpisodes = async () => {
  loading.value = true
  try {
    const res = await storyboardApi.getByProject(projectId)
    episodes.value = res.data
    if (completedEpisodes.value.length > 0 && !currentVideo.value) {
      selectVideo(completedEpisodes.value[0])
    }
  } catch (error) {
    console.error('Failed to load episodes:', error)
  } finally {
    loading.value = false
  }
}

const selectVideo = (ep) => {
  if (!ep.video_url) return
  currentVideo.value = ep
  currentIndex.value = completedEpisodes.value.findIndex(e => e.id === ep.id)
  isPlayingAll.value = false
}

const playPrevious = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    currentVideo.value = completedEpisodes.value[currentIndex.value]
  }
}

const playNext = () => {
  if (currentIndex.value < completedEpisodes.value.length - 1) {
    currentIndex.value++
    currentVideo.value = completedEpisodes.value[currentIndex.value]
  }
}

const togglePlayAll = () => {
  isPlayingAll.value = !isPlayingAll.value
  if (isPlayingAll.value && mainVideo.value) {
    mainVideo.value.play()
  } else if (mainVideo.value) {
    mainVideo.value.pause()
  }
}

const onVideoEnded = () => {
  if (isPlayingAll.value) {
    playNext()
    if (mainVideo.value && currentVideo.value) {
      setTimeout(() => mainVideo.value.play(), 100)
    }
  }
}

onMounted(loadEpisodes)

onUnmounted(() => {
  isPlayingAll.value = false
})
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
