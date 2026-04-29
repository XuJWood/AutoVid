<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold font-headline tracking-tight">剧集编辑</h1>
          <p class="text-sm text-on-surface-variant mt-1">每集~60秒/4个片段（5-15秒/段），每个片段生成一个视频（Seedance 视频+音频一体化）</p>
        </div>
        <div class="flex gap-3">
          <router-link
            :to="`/drama/${projectId}`"
            class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full text-sm font-medium hover:bg-surface-container-high transition-colors"
          >
            <span class="material-symbols-outlined text-sm">arrow_back</span>
            返回剧本
          </router-link>
          <button
            @click="generateEpisodes"
            :disabled="generating"
            class="flex items-center gap-2 bg-primary-container text-on-primary-container px-4 py-2 rounded-full text-sm font-bold hover:brightness-95 transition-all disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-sm">auto_awesome</span>
            {{ generating ? '生成中...' : '生成剧集' }}
          </button>
          <router-link
            v-if="episodes.length > 0"
            :to="`/drama/${projectId}/preview`"
            class="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-full text-sm font-bold hover:brightness-95 transition-all"
          >
            <span class="material-symbols-outlined text-sm">play_arrow</span>
            预览剧集
          </router-link>
        </div>
      </div>

      <!-- Stats Bar -->
      <div v-if="episodes.length > 0" class="bg-surface-container-low rounded-lg p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">movie</span>
              <span class="text-sm"><strong>{{ episodes.length }}</strong> 集</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-green-600">image</span>
              <span class="text-sm"><strong>{{ completedImages }}</strong> / {{ episodes.length }} 封面</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600">videocam</span>
              <span class="text-sm"><strong>{{ completedSegments }}</strong> / {{ totalSegments }} 片段视频</span>
            </div>
            <div v-if="videoConfigInfo" class="flex items-center gap-2">
              <span class="material-symbols-outlined text-purple-600">settings</span>
              <span class="text-sm text-on-surface-variant">{{ videoConfigInfo }}</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateAllSegmentsBatch"
              :disabled="generatingAll || totalSegments === 0"
              class="px-3 py-1.5 text-xs font-bold bg-primary text-on-primary rounded-full hover:brightness-95 transition-colors disabled:opacity-50"
            >
              {{ generatingAll ? '生成中...' : '一键生成全部片段视频' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Generation Progress -->
      <div v-if="generating || generatingAll" class="bg-primary/10 rounded-lg p-6 mb-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
            <span class="material-symbols-outlined text-primary animate-spin">autorenew</span>
          </div>
          <div class="flex-1">
            <h4 class="font-bold text-primary">{{ progressMessage }}</h4>
            <div class="w-full bg-surface-container-high rounded-full h-2 mt-2">
              <div
                class="bg-primary h-2 rounded-full transition-all duration-300"
                :style="{ width: progress + '%' }"
              ></div>
            </div>
          </div>
          <span class="text-sm font-bold text-primary">{{ progress }}%</span>
        </div>
      </div>

      <div v-if="errorMessage" class="bg-red-50 text-red-700 rounded-lg p-4 mb-6 text-sm flex items-start justify-between">
        <span class="whitespace-pre-wrap flex-1">{{ errorMessage }}</span>
        <button @click="errorMessage = ''" class="ml-4 flex-shrink-0 text-red-500 hover:text-red-700">
          <span class="material-symbols-outlined text-sm">close</span>
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="bg-surface-container-lowest rounded-lg p-12 text-center">
        <span class="material-symbols-outlined text-4xl text-primary animate-spin mb-3">autorenew</span>
        <p class="text-sm text-on-surface-variant">正在加载剧集数据...</p>
      </div>

      <!-- Episode List -->
      <div v-else-if="sortedEpisodes.length > 0" class="space-y-6">
        <div
          v-for="ep in sortedEpisodes"
          :key="ep.id"
          class="bg-surface-container-lowest rounded-lg p-6 shadow-sm"
        >
          <!-- Episode Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-1">
                <span class="bg-primary text-on-primary text-sm font-bold px-3 py-1 rounded-full">第{{ ep.episode_number }}集</span>
                <h3 class="text-lg font-bold">{{ ep.title || '未命名' }}</h3>
              </div>
              <p class="text-sm text-on-surface-variant mt-1">{{ ep.description }}</p>
              <div class="flex items-center gap-3 mt-2">
                <span class="text-xs text-on-surface-variant">目标时长: {{ ep.duration || 60 }}s</span>
                <span class="text-xs text-on-surface-variant">片段数: {{ (ep.segments || []).length }}</span>
              </div>
            </div>
            <!-- Status badges -->
            <div class="flex-shrink-0 flex items-center gap-2">
              <span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="statusBadgeClass(ep.image_status)">封面:{{ statusLabel(ep.image_status) }}</span>
            </div>
          </div>

          <!-- Episode Cover Preview -->
          <div class="aspect-video bg-surface-container rounded-lg overflow-hidden relative mb-6 max-w-md group">
            <img
              v-if="ep.image_url"
              :src="toPlayableUrl(ep.image_url)"
              class="w-full h-full object-cover"
              @error="(e) => e.target.style.display = 'none'"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <span class="material-symbols-outlined text-4xl text-on-surface-variant opacity-50">movie</span>
            </div>
          </div>

          <!-- Episode Actions -->
          <div class="flex gap-2 mb-4">
            <button
              @click="generateImage(ep)"
              :disabled="ep.image_status === 'processing'"
              class="flex-1 py-2 text-xs font-bold bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
            >
              {{ ep.image_url ? '重新生成封面' : '生成封面' }}
            </button>
            <button
              @click="generateAllSegments(ep)"
              :disabled="ep.image_status === 'processing' || generatingAll || !ep.segments?.length"
              class="flex-1 py-2 text-xs font-bold bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors disabled:opacity-50"
            >
              生成该集全部片段视频 ({{ pendingSegments(ep) }}个待生成)
            </button>
          </div>

          <!-- Segments Section -->
          <div v-if="ep.segments && ep.segments.length > 0">
            <p class="text-xs font-bold text-on-surface-variant mb-3 uppercase tracking-wider flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">view_module</span>
              片段列表（每个片段 = 1个视频）
            </p>
            <div class="space-y-3">
              <div
                v-for="seg in sortSegments(ep.segments)"
                :key="seg.id"
                class="bg-surface-container rounded-lg p-4"
                :class="seg.video_status === 'completed' ? 'border border-green-500/30' : ''"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-bold bg-primary/10 text-primary px-2 py-0.5 rounded">段{{ seg.segment_number }}</span>
                    <span v-if="seg.camera_movement" class="text-xs text-on-surface-variant flex items-center gap-1">
                      <span class="material-symbols-outlined text-xs">videocam</span>
                      {{ seg.camera_movement }}
                    </span>
                    <span class="text-xs font-bold text-on-surface-variant">脚本{{ seg.duration || 15 }}s</span>
                    <span
                      class="px-2 py-0.5 text-xs font-bold rounded-full flex items-center gap-1"
                      :class="statusBadgeClass(seg.video_status)"
                    >
                      <span v-if="seg.video_status === 'processing'" class="material-symbols-outlined text-xs animate-spin">autorenew</span>
                      {{ statusLabel(seg.video_status) }}
                    </span>
                  </div>
                </div>

                <!-- Segment content -->
                <p class="text-xs mb-2 leading-relaxed text-on-surface-variant">{{ seg.visual_description }}</p>
                <p v-if="seg.dialogue" class="text-xs text-primary bg-primary/5 p-2 rounded italic mb-2">
                  <span class="material-symbols-outlined text-xs align-middle">record_voice_over</span>
                  {{ seg.dialogue }}
                </p>

                <!-- Segment video preview -->
                <div v-if="seg.video_url" class="aspect-video bg-black rounded-lg overflow-hidden mb-2 max-w-sm">
                  <video
                    :src="toPlayableUrl(seg.video_url)"
                    class="w-full h-full object-contain"
                    controls
                    preload="metadata"
                  />
                </div>

                <!-- Segment actions -->
                <div class="flex gap-2">
                  <button
                    @click="generateSegmentVideo(seg)"
                    :disabled="seg.video_status === 'processing'"
                    class="text-xs font-bold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                    :class="seg.video_url ? 'bg-surface-container-high hover:bg-surface-container' : 'bg-blue-100 text-blue-800 hover:bg-blue-200'"
                  >
                    {{ seg.video_status === 'processing' ? '生成中...' : seg.video_url ? '重新生成' : '生成视频 (Seedance)' }}
                  </button>
                  <a
                    v-if="seg.video_url"
                    :href="toPlayableUrl(seg.video_url)"
                    download
                    class="flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors"
                    @click.stop
                  >
                    <span class="material-symbols-outlined text-sm">download</span>
                    下载
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-4 text-xs text-on-surface-variant/50">
            暂无片段数据，请先生成剧集
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-surface-container-lowest rounded-lg p-12 text-center">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-50 mb-4">movie_filter</span>
        <h3 class="text-lg font-bold mb-2">还没有剧集数据</h3>
        <p class="text-sm text-on-surface-variant mb-4">请先生成剧本，然后点击"生成剧集"按钮</p>
        <router-link
          :to="`/drama/${projectId}`"
          class="inline-flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-full text-sm font-bold hover:brightness-95 transition-all"
        >
          <span class="material-symbols-outlined text-sm">edit</span>
          去编辑剧本
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { storyboardApi } from '@/api/storyboard'
import { projectsApi } from '@/api/projects'
import { modelConfigApi } from '@/api/modelConfig'

const route = useRoute()
const projectId = route.params.id

const project = ref(null)
const episodes = ref([])
const loading = ref(true)
const generating = ref(false)
const generatingAll = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const errorMessage = ref('')
const videoConfigInfo = ref('')

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

function pendingSegments(ep) {
  return (ep.segments || []).filter(s => s.video_status !== 'completed').length
}

function statusBadgeClass(status) {
  switch (status) {
    case 'completed': return 'bg-green-500 text-white'
    case 'processing': return 'bg-yellow-500 text-white'
    case 'failed': return 'bg-red-500 text-white'
    case 'partial': return 'bg-orange-500 text-white'
    default: return 'bg-surface-container-high text-on-surface-variant'
  }
}

function statusLabel(status) {
  switch (status) {
    case 'completed': return '完成'
    case 'processing': return '处理中'
    case 'failed': return '失败'
    case 'partial': return '部分'
    default: return '待处理'
  }
}

const sortedEpisodes = computed(() => {
  return [...episodes.value].sort((a, b) => (a.episode_number || 0) - (b.episode_number || 0))
})

const completedImages = computed(() => episodes.value.filter(e => e.image_status === 'completed').length)

const allSegments = computed(() => {
  const segs = []
  for (const ep of episodes.value) {
    if (ep.segments) segs.push(...ep.segments)
  }
  return segs
})

const totalSegments = computed(() => allSegments.value.length)
const completedSegments = computed(() => allSegments.value.filter(s => s.video_status === 'completed').length)

const loadEpisodes = async () => {
  try {
    errorMessage.value = ''
    const res = await storyboardApi.getByProject(projectId)
    episodes.value = res.data
  } catch (error) {
    console.error('Failed to load episodes:', error)
    errorMessage.value = '加载剧集失败：' + (error.response?.data?.detail || error.message)
  }
}

const generateEpisodes = async () => {
  generating.value = true
  progress.value = 0
  progressMessage.value = '正在从剧本生成剧集和片段...'

  try {
    await storyboardApi.generate(projectId)
    progress.value = 100
    progressMessage.value = '剧集和片段生成成功！'
    await loadEpisodes()
  } catch (error) {
    console.error('Failed to generate episodes:', error)
    progressMessage.value = '生成失败：' + (error.response?.data?.detail || error.message)
  } finally {
    setTimeout(() => { generating.value = false }, 1000)
  }
}

const generateImage = async (ep) => {
  ep.image_status = 'processing'
  try {
    const res = await storyboardApi.generateImage(ep.id)
    if (res.data.status === 'completed') {
      ep.image_url = res.data.image_url
      ep.image_status = 'completed'
    } else {
      ep.image_status = 'failed'
    }
  } catch (error) {
    console.error('Failed to generate image:', error)
    ep.image_status = 'failed'
  }
}

const generateSegmentVideo = async (seg) => {
  seg.video_status = 'processing'
  errorMessage.value = ''
  try {
    const res = await storyboardApi.generateSegmentVideo(seg.id, {})
    if (res.data.status === 'completed') {
      seg.video_url = res.data.video_url
      seg.video_status = 'completed'
    } else {
      seg.video_status = 'failed'
      errorMessage.value = `片段${seg.segment_number}生成失败：` + (res.data.error || res.data.detail || '后端未返回可用视频')
    }
  } catch (error) {
    console.error('Failed to generate segment video:', error)
    seg.video_status = 'failed'
    const detail = error.response?.data?.error || error.response?.data?.detail || error.message
    errorMessage.value = `片段${seg.segment_number}生成失败：${detail}`
  }
}

const generateAllSegments = async (ep) => {
  generatingAll.value = true
  errorMessage.value = ''
  const segments = sortSegments(ep.segments || [])
  const pending = segments.filter(s => s.video_status !== 'completed')
  const errors = []

  for (let i = 0; i < pending.length; i++) {
    progress.value = Math.round((i / pending.length) * 100)
    progressMessage.value = `[第${ep.episode_number}集] 生成片段 ${i + 1}/${pending.length}`
    await generateSegmentVideo(pending[i])
    if (pending[i].video_status === 'failed') {
      errors.push(`段${pending[i].segment_number}`)
    }
  }

  progress.value = 100
  if (errors.length > 0) {
    progressMessage.value = `第${ep.episode_number}集 完成，${errors.length}个片段失败: ${errors.join(', ')}`
  } else {
    progressMessage.value = `第${ep.episode_number}集 全部片段生成成功！`
  }
  generatingAll.value = false

  const allDone = segments.every(s => s.video_status === 'completed')
  if (allDone) {
    ep.video_status = 'completed'
  }
}

const generateAllSegmentsBatch = async () => {
  generatingAll.value = true
  errorMessage.value = ''
  let failCount = 0
  let successCount = 0

  for (const ep of sortedEpisodes.value) {
    const segments = sortSegments(ep.segments || [])
    const pending = segments.filter(s => s.video_status !== 'completed')
    if (pending.length === 0) continue

    for (let i = 0; i < pending.length; i++) {
      progress.value = Math.round((completedSegments.value / totalSegments.value) * 100)
      progressMessage.value = `[第${ep.episode_number}集] 生成片段 ${i + 1}/${pending.length}`
      await generateSegmentVideo(pending[i])
      if (pending[i].video_status === 'completed') {
        successCount++
      } else {
        failCount++
      }
    }
  }
  progress.value = 100
  if (failCount > 0) {
    progressMessage.value = `生成完成：${successCount}个成功，${failCount}个失败`
  } else {
    progressMessage.value = '全部片段视频生成完成！'
  }
  generatingAll.value = false
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await projectsApi.get(projectId)
    project.value = res.data
  } catch (e) {
    console.error('Failed to load project:', e)
  }
  try {
    const vcRes = await modelConfigApi.getByName('video')
    const vc = vcRes.data
    const p = vc.params || {}
    videoConfigInfo.value = `${vc.model || '未配置'} · ${p.duration || 5}s · ${p.resolution || '720p'} · ${p.ratio || '16:9'}`
  } catch (e) {
    // ignore
  }
  await loadEpisodes()
  loading.value = false
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
