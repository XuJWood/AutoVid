<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold font-headline tracking-tight">视频预览</h1>
          <p class="text-sm text-on-surface-variant mt-1">每集多个片段，每个片段独立视频 — 点击播放，支持连续播放</p>
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
              <span class="material-symbols-outlined text-primary">movie</span>
              <span class="text-sm"><strong>{{ episodes.length }}</strong> 集</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600">videocam</span>
              <span class="text-sm"><strong>{{ completedSegmentVideos }}</strong> / {{ totalSegmentVideos }} 片段视频已生成</span>
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

      <!-- Loading -->
      <div v-if="loading" class="bg-surface-container-lowest rounded-lg p-12 text-center">
        <span class="material-symbols-outlined text-4xl text-primary animate-spin mb-3">autorenew</span>
        <p class="text-sm text-on-surface-variant">正在加载剧集数据...</p>
      </div>

      <!-- Main Content -->
      <div v-else class="grid grid-cols-12 gap-6">
        <!-- Left: Video Player with Cover -->
        <div class="col-span-12 lg:col-span-8">
          <div class="bg-surface-container-lowest rounded-lg overflow-hidden shadow-sm">
            <!-- Player Area: Cover-first design -->
            <div class="aspect-video bg-black relative">
              <!-- Cover Image Overlay (shown before play) -->
              <div
                v-if="currentSegment && !videoPlaying"
                class="absolute inset-0 z-10 cursor-pointer group"
                @click="startPlayback"
              >
                <img
                  v-if="currentEpImage && !imageError"
                  :src="toPlayableUrl(currentEpImage)"
                  class="w-full h-full object-cover"
                  @error="onImageError"
                />
                <div v-if="!currentEpImage || imageError" class="w-full h-full flex items-center justify-center bg-surface-container">
                  <span class="material-symbols-outlined text-6xl text-on-surface-variant/30">movie</span>
                </div>
                <div class="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/30 transition-colors">
                  <div class="w-20 h-20 rounded-full bg-primary/90 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-primary/40">
                    <span class="material-symbols-outlined text-white text-4xl">play_arrow</span>
                  </div>
                </div>
                <div class="absolute top-4 left-4 bg-black/60 text-white px-3 py-1.5 rounded-full text-sm font-bold">
                  第{{ currentEp?.episode_number }}集 · 段{{ currentSegment.segment_number }}
                </div>
              </div>

              <!-- Video Element -->
              <video
                v-if="currentSegment"
                ref="mainVideo"
                :src="toPlayableUrl(currentSegment.video_url)"
                :poster="currentEpImage ? toPlayableUrl(currentEpImage) : undefined"
                class="w-full h-full object-contain"
                :class="{ 'opacity-0': !videoPlaying }"
                controls
                @ended="onVideoEnded"
                @play="videoPlaying = true"
                @pause="onVideoPause"
              ></video>

              <!-- No video selected -->
              <div v-if="!currentSegment" class="w-full h-full flex items-center justify-center">
                <div class="text-center text-white/60">
                  <span class="material-symbols-outlined text-6xl mb-2">play_circle</span>
                  <p class="text-sm">选择一个片段开始预览</p>
                </div>
              </div>

              <!-- Video info bar -->
              <div v-if="currentSegment && videoPlaying" class="absolute bottom-4 left-4 right-4 bg-black/60 text-white px-3 py-2 rounded-lg backdrop-blur-sm">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-xs font-bold">第{{ currentEp?.episode_number }}集 · 段{{ currentSegment.segment_number }}</span>
                    <span v-if="currentSegment.dialogue" class="ml-2 text-xs opacity-80">{{ currentSegment.dialogue.substring(0, 50) }}...</span>
                  </div>
                  <span class="text-xs font-bold">{{ currentSegment.duration || 15 }}s</span>
                </div>
              </div>
            </div>

            <!-- Playback Controls -->
            <div v-if="allCompletedSegments.length > 0" class="p-4 border-t border-surface-container">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <button
                    @click="playPrevious"
                    :disabled="currentSegIndex <= 0"
                    class="p-2 rounded-full hover:bg-surface-container transition-colors disabled:opacity-30"
                    title="上一段"
                  >
                    <span class="material-symbols-outlined">skip_previous</span>
                  </button>
                  <button
                    @click="togglePlayPause"
                    class="p-3 bg-primary text-on-primary rounded-full hover:brightness-95 transition-all"
                    :title="videoPlaying ? '暂停' : '播放'"
                  >
                    <span class="material-symbols-outlined">{{ videoPlaying ? 'pause' : 'play_arrow' }}</span>
                  </button>
                  <button
                    @click="playNext"
                    :disabled="currentSegIndex >= allCompletedSegments.length - 1"
                    class="p-2 rounded-full hover:bg-surface-container transition-colors disabled:opacity-30"
                    title="下一段"
                  >
                    <span class="material-symbols-outlined">skip_next</span>
                  </button>
                  <button
                    @click="isPlayingAll = !isPlayingAll"
                    class="p-2 rounded-full transition-colors"
                    :class="isPlayingAll ? 'bg-primary/10 text-primary' : 'hover:bg-surface-container'"
                    :title="isPlayingAll ? '取消连播' : '连续播放'"
                  >
                    <span class="material-symbols-outlined text-sm">{{ isPlayingAll ? 'repeat_on' : 'repeat' }}</span>
                  </button>
                </div>
                <div class="flex items-center gap-4">
                  <span class="text-sm text-on-surface-variant">{{ currentSegIndex + 1 }} / {{ allCompletedSegments.length }}</span>
                  <span v-if="isPlayingAll" class="text-primary text-sm font-bold">连续播放中</span>
                  <a
                    v-if="currentSegment?.video_url"
                    :href="toPlayableUrl(currentSegment.video_url)"
                    download
                    class="flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-primary/10 text-primary rounded-full hover:bg-primary/20 transition-colors"
                  >
                    <span class="material-symbols-outlined text-sm">download</span>
                    下载本段
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Episode & Segment List -->
        <div class="col-span-12 lg:col-span-4">
          <div class="bg-surface-container-lowest rounded-lg shadow-sm">
            <div class="p-4 border-b border-surface-container">
              <h3 class="font-bold text-sm">剧集 & 片段列表</h3>
            </div>

            <div class="max-h-[600px] overflow-y-auto custom-scrollbar">
              <div v-if="sortedEpisodes.length > 0" class="p-4">
                <div v-for="ep in sortedEpisodes" :key="ep.id" class="mb-4 last:mb-0">
                  <!-- Episode header -->
                  <div class="flex items-center gap-2 mb-2">
                    <span class="text-xs font-bold bg-primary/10 text-primary px-2 py-0.5 rounded">第{{ ep.episode_number }}集</span>
                    <span class="text-xs font-bold text-on-surface truncate">{{ ep.title || '未命名' }}</span>
                    <span class="text-xs text-on-surface-variant ml-auto">{{ (ep.segments || []).length }}段</span>
                  </div>

                  <!-- Episode segments -->
                  <div v-if="ep.segments && ep.segments.length > 0" class="space-y-1.5 ml-2">
                    <button
                      v-for="seg in sortSegments(ep.segments)"
                      :key="seg.id"
                      @click="selectSegment(ep, seg)"
                      :disabled="!seg.video_url"
                      class="w-full flex items-center gap-2 p-2 rounded-lg transition-colors text-left"
                      :class="[
                        currentSegment?.id === seg.id ? 'bg-primary/10 border border-primary/30' : 'hover:bg-surface-container-low',
                        !seg.video_url ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                      ]"
                    >
                      <!-- Thumbnail -->
                      <div class="w-16 h-10 bg-surface-container rounded overflow-hidden flex-shrink-0 relative">
                        <img
                          v-if="ep.image_url"
                          :src="toPlayableUrl(ep.image_url)"
                          class="w-full h-full object-cover"
                          @error="(e) => e.target.style.display = 'none'"
                        />
                        <div v-else class="w-full h-full flex items-center justify-center">
                          <span class="material-symbols-outlined text-xs text-on-surface-variant">movie</span>
                        </div>
                        <div v-if="seg.video_url" class="absolute inset-0 bg-black/20 flex items-center justify-center">
                          <span class="material-symbols-outlined text-white text-sm">play_circle</span>
                        </div>
                      </div>

                      <!-- Info -->
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-1">
                          <span class="text-xs font-bold">段{{ seg.segment_number }}</span>
                          <span v-if="seg.video_url" class="material-symbols-outlined text-xs text-green-600">check_circle</span>
                          <span v-else class="material-symbols-outlined text-xs text-on-surface-variant/30">pending</span>
                        </div>
                        <div class="text-xs text-on-surface-variant truncate">
                          {{ seg.dialogue || seg.visual_description?.substring(0, 30) || '暂无描述' }}
                        </div>
                        <div class="text-xs text-on-surface-variant">{{ seg.duration || 15 }}s</div>
                      </div>

                      <!-- Download -->
                      <a
                        v-if="seg.video_url"
                        :href="toPlayableUrl(seg.video_url)"
                        download
                        class="flex-shrink-0 p-1.5 hover:bg-surface-container rounded-full transition-colors"
                        @click.stop
                        title="下载"
                      >
                        <span class="material-symbols-outlined text-sm text-primary">download</span>
                      </a>
                    </button>
                  </div>
                  <div v-else class="text-xs text-on-surface-variant/50 ml-2 py-1">暂无片段数据</div>
                </div>
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { storyboardApi } from '@/api/storyboard'

const route = useRoute()
const projectId = route.params.id

const episodes = ref([])
const loading = ref(true)
const currentSegment = ref(null)
const currentEp = ref(null)
const currentEpImage = ref(null)
const currentSegIndex = ref(0)
const isPlayingAll = ref(false)
const videoPlaying = ref(false)
const mainVideo = ref(null)
const imageError = ref(false)

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

function sortSegments(segments) {
  return [...segments].sort((a, b) => (a.segment_number || 0) - (b.segment_number || 0))
}

const sortedEpisodes = computed(() => {
  return [...episodes.value].sort((a, b) => (a.episode_number || 0) - (b.episode_number || 0))
})

const allCompletedSegments = computed(() => {
  const segs = []
  for (const ep of sortedEpisodes.value) {
    if (ep.segments) {
      for (const seg of sortSegments(ep.segments)) {
        if (seg.video_url) {
          segs.push({ ...seg, _ep: ep })
        }
      }
    }
  }
  return segs
})

const totalSegmentVideos = computed(() => {
  let count = 0
  for (const ep of episodes.value) {
    if (ep.segments) count += ep.segments.length
  }
  return count
})

const completedSegmentVideos = computed(() => allCompletedSegments.value.length)

const totalDuration = computed(() => {
  let dur = 0
  for (const seg of allCompletedSegments.value) {
    dur += seg.duration || 15
  }
  return dur
})

const progressPercent = computed(() => {
  if (totalSegmentVideos.value === 0) return 0
  return Math.round((completedSegmentVideos.value / totalSegmentVideos.value) * 100)
})

const loadEpisodes = async () => {
  loading.value = true
  try {
    const res = await storyboardApi.getByProject(projectId)
    episodes.value = res.data
    // Auto-select first completed segment
    if (allCompletedSegments.value.length > 0 && !currentSegment.value) {
      const first = allCompletedSegments.value[0]
      selectSegment(first._ep, first)
    }
  } catch (error) {
    console.error('Failed to load episodes:', error)
  } finally {
    loading.value = false
  }
}

const selectSegment = (ep, seg) => {
  if (!seg.video_url) return
  videoPlaying.value = false
  imageError.value = false
  currentEp.value = ep
  currentEpImage.value = ep.image_url
  currentSegment.value = seg
  currentSegIndex.value = allCompletedSegments.value.findIndex(s => s.id === seg.id)
  isPlayingAll.value = false
}

const startPlayback = () => {
  videoPlaying.value = true
  if (mainVideo.value) {
    mainVideo.value.play().catch(e => console.error('Playback failed:', e))
  }
}

const togglePlayPause = () => {
  if (!mainVideo.value) return
  if (videoPlaying.value) {
    mainVideo.value.pause()
  } else {
    if (!currentSegment.value && allCompletedSegments.value.length > 0) {
      const first = allCompletedSegments.value[0]
      selectSegment(first._ep, first)
    }
    startPlayback()
  }
}

const onVideoPause = () => {
  videoPlaying.value = !mainVideo.value?.paused
}

const playPrevious = () => {
  if (currentSegIndex.value > 0) {
    currentSegIndex.value--
    const seg = allCompletedSegments.value[currentSegIndex.value]
    if (seg) {
      videoPlaying.value = false
      currentEp.value = seg._ep
      currentEpImage.value = seg._ep?.image_url
      currentSegment.value = seg
    }
  }
}

const playNext = () => {
  if (currentSegIndex.value < allCompletedSegments.value.length - 1) {
    currentSegIndex.value++
    const seg = allCompletedSegments.value[currentSegIndex.value]
    if (seg) {
      videoPlaying.value = false
      currentEp.value = seg._ep
      currentEpImage.value = seg._ep?.image_url
      currentSegment.value = seg
    }
  } else {
    isPlayingAll.value = false
  }
}

const onVideoEnded = () => {
  if (isPlayingAll.value) {
    playNext()
    if (mainVideo.value && currentSegment.value) {
      setTimeout(() => {
        videoPlaying.value = true
        mainVideo.value.play().catch(() => {})
      }, 300)
    }
  } else {
    videoPlaying.value = false
  }
}

const onImageError = () => {
  imageError.value = true
}

watch(currentSegment, () => {
  videoPlaying.value = false
  imageError.value = false
})

onMounted(loadEpisodes)

onUnmounted(() => {
  isPlayingAll.value = false
  videoPlaying.value = false
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
