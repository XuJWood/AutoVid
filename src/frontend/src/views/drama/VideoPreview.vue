<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold font-headline tracking-tight">视频预览</h1>
          <p class="text-sm text-on-surface-variant mt-1">预览和导出完整视频</p>
        </div>
        <div class="flex gap-3">
          <router-link
            :to="`/drama/${projectId}/storyboard`"
            class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full text-sm font-medium hover:bg-surface-container-high transition-colors"
          >
            <span class="material-symbols-outlined text-sm">arrow_back</span>
            返回分镜
          </router-link>
          <button
            @click="exportVideo"
            :disabled="!canExport || exporting"
            class="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-full text-sm font-bold hover:brightness-95 transition-all disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-sm">{{ exporting ? 'sync' : 'download' }}</span>
            {{ exporting ? '导出中...' : '导出视频' }}
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="bg-surface-container-low rounded-lg p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600">videocam</span>
              <span class="text-sm"><strong>{{ completedVideos }}</strong> / {{ totalShots }} 视频已生成</span>
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

      <!-- Main Content -->
      <div class="grid grid-cols-12 gap-6">
        <!-- Left: Video Player -->
        <div class="col-span-12 lg:col-span-8">
          <div class="bg-surface-container-lowest rounded-lg overflow-hidden shadow-sm">
            <!-- Main Video -->
            <div class="aspect-video bg-black relative">
              <video
                v-if="currentVideo"
                ref="mainVideo"
                :src="currentVideo.video_url"
                class="w-full h-full object-contain"
                controls
                @ended="onVideoEnded"
              ></video>
              <div v-else class="w-full h-full flex items-center justify-center">
                <div class="text-center text-white/60">
                  <span class="material-symbols-outlined text-6xl mb-2">play_circle</span>
                  <p class="text-sm">选择一个镜头开始预览</p>
                </div>
              </div>

              <!-- Video Overlay Info -->
              <div v-if="currentVideo" class="absolute bottom-4 left-4 right-4 bg-black/60 text-white px-3 py-2 rounded">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-xs font-bold">场景 {{ currentVideo.scene_index + 1 }} · 镜头 {{ currentVideo.shot_index + 1 }}</span>
                    <p class="text-xs opacity-80 line-clamp-1">{{ currentVideo.description }}</p>
                  </div>
                  <span class="text-xs font-bold">{{ currentVideo.duration }}s</span>
                </div>
              </div>
            </div>

            <!-- Playback Controls -->
            <div v-if="storyboards.length > 0" class="p-4 border-t border-surface-container">
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
                    :disabled="currentIndex >= completedStoryboards.length - 1"
                    class="p-2 rounded-full hover:bg-surface-container transition-colors disabled:opacity-30"
                  >
                    <span class="material-symbols-outlined">skip_next</span>
                  </button>
                </div>
                <div class="flex items-center gap-4 text-sm text-on-surface-variant">
                  <span>{{ currentIndex + 1 }} / {{ completedStoryboards.length }}</span>
                  <span v-if="isPlayingAll" class="text-primary font-bold">连续播放中</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Export Options -->
          <div class="bg-surface-container-low rounded-lg p-4 mt-4">
            <h3 class="font-bold text-sm mb-3">导出选项</h3>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="text-xs text-on-surface-variant block mb-1">分辨率</label>
                <select v-model="exportOptions.resolution" class="w-full bg-surface-container-lowest border border-surface-container rounded px-3 py-2 text-sm">
                  <option value="1080p">1080p (Full HD)</option>
                  <option value="720p">720p (HD)</option>
                  <option value="480p">480p (SD)</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-on-surface-variant block mb-1">帧率</label>
                <select v-model="exportOptions.fps" class="w-full bg-surface-container-lowest border border-surface-container rounded px-3 py-2 text-sm">
                  <option value="30">30 FPS</option>
                  <option value="24">24 FPS (电影)</option>
                  <option value="60">60 FPS</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-on-surface-variant block mb-1">格式</label>
                <select v-model="exportOptions.format" class="w-full bg-surface-container-lowest border border-surface-container rounded px-3 py-2 text-sm">
                  <option value="mp4">MP4</option>
                  <option value="mov">MOV</option>
                  <option value="webm">WebM</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Timeline -->
        <div class="col-span-12 lg:col-span-4">
          <div class="bg-surface-container-lowest rounded-lg shadow-sm">
            <div class="p-4 border-b border-surface-container">
              <h3 class="font-bold text-sm">时间线</h3>
            </div>

            <div class="max-h-[600px] overflow-y-auto custom-scrollbar">
              <div v-if="groupedStoryboards.length > 0" class="divide-y divide-surface-container">
                <div v-for="group in groupedStoryboards" :key="group.sceneIndex" class="p-4">
                  <h4 class="text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-3">
                    场景 {{ group.sceneIndex + 1 }}
                  </h4>
                  <div class="space-y-2">
                    <button
                      v-for="shot in group.shots"
                      :key="shot.id"
                      @click="selectVideo(shot)"
                      :disabled="!shot.video_url"
                      class="w-full flex items-center gap-3 p-2 rounded-lg transition-colors"
                      :class="[
                        currentVideo?.id === shot.id ? 'bg-primary/10 border border-primary/30' : 'hover:bg-surface-container-low',
                        !shot.video_url ? 'opacity-50 cursor-not-allowed' : ''
                      ]"
                    >
                      <!-- Thumbnail -->
                      <div class="w-16 h-10 bg-surface-container rounded overflow-hidden flex-shrink-0">
                        <img
                          v-if="shot.image_url"
                          :src="shot.image_url"
                          class="w-full h-full object-cover"
                        />
                        <span v-else class="material-symbols-outlined text-sm text-on-surface-variant">image</span>
                      </div>

                      <!-- Info -->
                      <div class="flex-1 text-left">
                        <div class="text-xs font-bold">镜头 {{ shot.shot_index + 1 }}</div>
                        <div class="text-xs text-on-surface-variant line-clamp-1">{{ shot.description }}</div>
                      </div>

                      <!-- Status -->
                      <div class="flex-shrink-0">
                        <span v-if="shot.video_url" class="material-symbols-outlined text-sm text-green-600">check_circle</span>
                        <span v-else-if="shot.status === 'processing'" class="material-symbols-outlined text-sm text-yellow-600 animate-spin">sync</span>
                        <span v-else class="material-symbols-outlined text-sm text-on-surface-variant opacity-50">pending</span>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              <div v-else class="p-8 text-center text-on-surface-variant">
                <span class="material-symbols-outlined text-4xl opacity-50 mb-2">movie_filter</span>
                <p class="text-sm">还没有分镜数据</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Progress Modal -->
      <div v-if="exporting" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-surface rounded-lg p-6 max-w-md w-full mx-4">
          <h3 class="font-bold text-lg mb-4">正在导出视频</h3>
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary animate-spin">sync</span>
              <span class="text-sm">{{ exportProgress }}</span>
            </div>
            <div class="w-full bg-surface-container-high rounded-full h-2">
              <div
                class="bg-primary h-2 rounded-full transition-all"
                :style="{ width: exportPercent + '%' }"
              ></div>
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

const storyboards = ref([])
const currentVideo = ref(null)
const currentIndex = ref(0)
const isPlayingAll = ref(false)
const mainVideo = ref(null)

const exporting = ref(false)
const exportPercent = ref(0)
const exportProgress = ref('准备导出...')

const exportOptions = ref({
  resolution: '1080p',
  fps: '30',
  format: 'mp4'
})

// Computed
const completedStoryboards = computed(() => {
  return storyboards.value.filter(sb => sb.video_url)
})

const totalShots = computed(() => storyboards.value.length)

const completedVideos = computed(() => completedStoryboards.value.length)

const totalDuration = computed(() => {
  return storyboards.value.reduce((sum, sb) => sum + (sb.duration || 0), 0)
})

const progressPercent = computed(() => {
  if (totalShots.value === 0) return 0
  return Math.round((completedVideos.value / totalShots.value) * 100)
})

const canExport = computed(() => {
  return completedVideos.value > 0 && completedVideos.value === totalShots.value
})

const groupedStoryboards = computed(() => {
  const groups = {}
  storyboards.value.forEach(sb => {
    const key = sb.scene_index
    if (!groups[key]) {
      groups[key] = {
        sceneIndex: sb.scene_index,
        shots: []
      }
    }
    groups[key].shots.push(sb)
  })
  return Object.values(groups).sort((a, b) => a.sceneIndex - b.sceneIndex)
})

// Methods
const loadStoryboards = async () => {
  try {
    const res = await storyboardApi.getByProject(projectId)
    storyboards.value = res.data
    // Auto-select first completed video
    if (completedStoryboards.value.length > 0 && !currentVideo.value) {
      selectVideo(completedStoryboards.value[0])
    }
  } catch (error) {
    console.error('Failed to load storyboards:', error)
  }
}

const selectVideo = (shot) => {
  if (!shot.video_url) return
  currentVideo.value = shot
  currentIndex.value = completedStoryboards.value.findIndex(s => s.id === shot.id)
  isPlayingAll.value = false
}

const playPrevious = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    currentVideo.value = completedStoryboards.value[currentIndex.value]
  }
}

const playNext = () => {
  if (currentIndex.value < completedStoryboards.value.length - 1) {
    currentIndex.value++
    currentVideo.value = completedStoryboards.value[currentIndex.value]
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

const exportVideo = async () => {
  if (!canExport.value) return

  exporting.value = true
  exportPercent.value = 0
  exportProgress.value = '正在合并视频片段...'

  // Simulate export progress
  const interval = setInterval(() => {
    if (exportPercent.value < 90) {
      exportPercent.value += 10
    }
  }, 500)

  try {
    // TODO: Call backend export API
    // const res = await api.post(`/projects/${projectId}/export`, exportOptions.value)

    // Simulate export completion
    await new Promise(resolve => setTimeout(resolve, 5000))

    exportPercent.value = 100
    exportProgress.value = '导出完成！'

    setTimeout(() => {
      exporting.value = false
      // TODO: Trigger download
      alert('视频导出成功！下载将自动开始。')
    }, 1000)

  } catch (error) {
    console.error('Failed to export video:', error)
    exportProgress.value = '导出失败：' + error.message
    setTimeout(() => {
      exporting.value = false
    }, 2000)
  } finally {
    clearInterval(interval)
  }
}

onMounted(loadStoryboards)

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
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
