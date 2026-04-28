<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold font-headline tracking-tight">剧集编辑</h1>
          <p class="text-sm text-on-surface-variant mt-1">封面 → 配音 → 视频（i2v 口型同步流水线）</p>
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
              <span class="material-symbols-outlined text-purple-600">volume_up</span>
              <span class="text-sm"><strong>{{ completedAudios }}</strong> / {{ episodes.length }} 配音</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600">videocam</span>
              <span class="text-sm"><strong>{{ completedVideos }}</strong> / {{ episodes.length }} 视频</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateAllPipeline"
              :disabled="generatingAll"
              class="px-3 py-1.5 text-xs font-bold bg-primary-container text-on-primary-container rounded-full hover:brightness-95 transition-colors disabled:opacity-50"
            >
              一键生成全部（封面→配音→视频）
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
        <p v-if="generatingAll && batchTotal > 0" class="text-xs text-on-surface-variant mt-2 text-center">
          {{ batchCurrent }} / {{ batchTotal }} 个步骤完成
        </p>
      </div>

      <!-- Loading State -->
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
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-1">
                <span class="bg-primary text-on-primary text-sm font-bold px-3 py-1 rounded-full">第{{ ep.episode_number }}集</span>
                <h3 class="text-lg font-bold">{{ ep.title || '未命名' }}</h3>
              </div>
              <p class="text-sm text-on-surface-variant mt-1">{{ ep.description }}</p>
              <div class="flex items-center gap-3 mt-2">
                <span class="text-xs text-on-surface-variant">目标时长: {{ ep.duration }}s</span>
                <span v-if="ep.episode_script" class="text-xs text-on-surface-variant">
                  剧本: {{ ep.episode_script.substring(0, 80) }}{{ ep.episode_script.length > 80 ? '...' : '' }}
                </span>
              </div>
            </div>
            <!-- Stage Status Badges -->
            <div class="flex-shrink-0 flex items-center gap-2">
              <span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="statusBadgeClass(ep.image_status)">封面:{{ statusLabel(ep.image_status) }}</span>
              <span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="statusBadgeClass(ep.audio_status)">配音:{{ statusLabel(ep.audio_status) }}</span>
              <span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="statusBadgeClass(ep.video_status)">视频:{{ statusLabel(ep.video_status) }}</span>
            </div>
          </div>

          <!-- Preview Area -->
          <div class="aspect-video bg-surface-container rounded-lg overflow-hidden relative mb-4 max-w-md">
            <div
              v-if="ep.video_status === 'processing'"
              class="absolute inset-0 bg-black/40 flex items-center justify-center z-10"
            >
              <div class="text-center">
                <span class="material-symbols-outlined text-3xl text-white animate-spin">autorenew</span>
                <p class="text-xs text-white mt-1">视频生成中...</p>
              </div>
            </div>
            <video
              v-if="ep.video_url"
              :src="toPlayableUrl(ep.video_url)"
              :poster="ep.image_url ? toPlayableUrl(ep.image_url) : undefined"
              class="w-full h-full object-cover"
              controls
            />
            <img
              v-else-if="ep.image_url"
              :src="toPlayableUrl(ep.image_url)"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <span class="material-symbols-outlined text-4xl text-on-surface-variant opacity-50">movie</span>
            </div>
          </div>

          <!-- Audio Preview -->
          <div v-if="ep.audio_url" class="mb-4 bg-surface-container rounded-lg p-3 max-w-md">
            <p class="text-xs font-bold text-on-surface-variant mb-2 uppercase tracking-wider">配音预览</p>
            <audio :src="toPlayableUrl(ep.audio_url)" controls class="w-full" style="height: 32px;" />
          </div>

          <!-- Dialogue Preview -->
          <div v-if="ep.dialogue_lines && ep.dialogue_lines.length > 0" class="mb-4">
            <p class="text-xs font-bold text-on-surface-variant mb-2 uppercase tracking-wider">对话</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(d, dIdx) in ep.dialogue_lines"
                :key="dIdx"
                class="text-xs bg-primary/5 text-on-surface px-2 py-1 rounded"
              >
                <strong>{{ d.speaker }}</strong>: {{ d.text }}
              </span>
            </div>
          </div>

          <!-- Actions: Cover → Audio → Video (i2v correct order) -->
          <div class="flex gap-2">
            <button
              @click="generateImage(ep)"
              :disabled="ep.image_status === 'processing' || ep.audio_status === 'processing' || ep.video_status === 'processing'"
              class="flex-1 py-2 text-xs font-bold bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
            >
              {{ ep.image_url ? '重新生成封面' : '① 生成封面' }}
            </button>
            <button
              @click="generateAudio(ep)"
              :disabled="ep.image_status === 'processing' || ep.audio_status === 'processing' || ep.video_status === 'processing'"
              class="flex-1 py-2 text-xs font-bold bg-purple-100 text-purple-800 rounded-lg hover:bg-purple-200 transition-colors disabled:opacity-50"
            >
              {{ ep.audio_url ? '重新配音' : '② 配音' }}
            </button>
            <button
              @click="generateVideo(ep)"
              :disabled="ep.image_status === 'processing' || ep.audio_status === 'processing' || ep.video_status === 'processing'"
              class="flex-1 py-2 text-xs font-bold bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors disabled:opacity-50"
            >
              {{ ep.video_url ? '重新生成视频' : '③ 生成视频' }}
            </button>
            <a
              v-if="ep.video_url"
              :href="toPlayableUrl(ep.video_url)"
              download
              class="flex items-center gap-1 px-3 py-2 text-xs font-bold bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors"
            >
              <span class="material-symbols-outlined text-sm">download</span>
              下载
            </a>
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

const route = useRoute()
const projectId = route.params.id

const project = ref(null)
const episodes = ref([])
const loading = ref(true)
const generating = ref(false)
const generatingAll = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const batchCurrent = ref(0)
const batchTotal = ref(0)

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

function statusBadgeClass(status) {
  switch (status) {
    case 'completed': return 'bg-green-500 text-white'
    case 'processing': return 'bg-yellow-500 text-white'
    case 'failed': return 'bg-red-500 text-white'
    default: return 'bg-surface-container-high text-on-surface-variant'
  }
}

function statusLabel(status) {
  switch (status) {
    case 'completed': return '完成'
    case 'processing': return '处理中'
    case 'failed': return '失败'
    default: return '待处理'
  }
}

const sortedEpisodes = computed(() => {
  return [...episodes.value].sort((a, b) => (a.episode_number || 0) - (b.episode_number || 0))
})

const completedImages = computed(() => episodes.value.filter(e => e.image_status === 'completed').length)
const completedVideos = computed(() => episodes.value.filter(e => e.video_status === 'completed').length)
const completedAudios = computed(() => episodes.value.filter(e => e.audio_status === 'completed').length)

const loadProject = async () => {
  try {
    const res = await projectsApi.get(projectId)
    project.value = res.data
  } catch (error) {
    console.error('Failed to load project:', error)
  }
}

const loadEpisodes = async () => {
  try {
    const res = await storyboardApi.getByProject(projectId)
    episodes.value = res.data
  } catch (error) {
    console.error('Failed to load episodes:', error)
  }
}

const generateEpisodes = async () => {
  generating.value = true
  progress.value = 0
  progressMessage.value = '正在从剧本生成剧集...'

  try {
    await storyboardApi.generate(projectId)
    progress.value = 100
    progressMessage.value = '剧集生成成功！'
    await loadEpisodes()
  } catch (error) {
    console.error('Failed to generate episodes:', error)
    progressMessage.value = '生成失败：' + (error.response?.data?.detail || error.message)
  } finally {
    setTimeout(() => {
      generating.value = false
    }, 1000)
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

const generateAudio = async (ep) => {
  ep.audio_status = 'processing'
  try {
    let dialogue = ''
    if (ep.dialogue_lines && Array.isArray(ep.dialogue_lines)) {
      dialogue = ep.dialogue_lines.map(d => {
        if (typeof d === 'object') return `${d.speaker || ''}: ${d.text || ''}`
        return String(d)
      }).join('。')
    }
    const res = await storyboardApi.generateAudio(ep.id, dialogue, null)
    if (res.data.status === 'completed') {
      ep.audio_url = res.data.audio_url
      ep.audio_status = 'completed'
    } else {
      ep.audio_status = 'failed'
    }
  } catch (error) {
    console.error('Failed to generate audio:', error)
    ep.audio_status = 'failed'
  }
}

const generateVideo = async (ep) => {
  ep.video_status = 'processing'
  try {
    const res = await storyboardApi.generateVideo(ep.id, {
      audio_url: ep.audio_url || null,
      duration: ep.duration || 15
    })
    if (res.data.status === 'completed') {
      ep.video_url = res.data.video_url
      ep.video_status = 'completed'
    } else {
      ep.video_status = 'failed'
    }
  } catch (error) {
    console.error('Failed to generate video:', error)
    ep.video_status = 'failed'
  }
}

const generateAllPipeline = async () => {
  generatingAll.value = true
  const episodesToProcess = episodes.value.filter(
    e => e.image_status !== 'processing' && e.audio_status !== 'processing' && e.video_status !== 'processing'
  )
  const totalSteps = episodesToProcess.length * 3
  batchTotal.value = totalSteps
  batchCurrent.value = 0

  for (const ep of episodesToProcess) {
    // Step 1: Cover image
    if (!ep.image_url || ep.image_status === 'failed') {
      batchCurrent.value++
      progressMessage.value = `[第${ep.episode_number}集] 生成封面 (${batchCurrent.value}/${batchTotal.value})`
      progress.value = Math.round((batchCurrent.value / batchTotal.value) * 100)
      await generateImage(ep)
      if (ep.image_status === 'failed') continue
    } else {
      batchCurrent.value++
    }

    // Step 2: Audio (TTS)
    if (!ep.audio_url || ep.audio_status === 'failed') {
      batchCurrent.value++
      progressMessage.value = `[第${ep.episode_number}集] 生成配音 (${batchCurrent.value}/${batchTotal.value})`
      progress.value = Math.round((batchCurrent.value / batchTotal.value) * 100)
      await generateAudio(ep)
      if (ep.audio_status === 'failed') continue
    } else {
      batchCurrent.value++
    }

    // Step 3: Video (i2v with first_frame + driving_audio)
    batchCurrent.value++
    progressMessage.value = `[第${ep.episode_number}集] 生成视频 (${batchCurrent.value}/${batchTotal.value})`
    progress.value = Math.round((batchCurrent.value / batchTotal.value) * 100)
    await generateVideo(ep)
  }

  progress.value = 100
  progressMessage.value = `全部完成！`
  generatingAll.value = false
  setTimeout(() => {
    batchCurrent.value = 0
    batchTotal.value = 0
  }, 1500)
}

onMounted(async () => {
  loading.value = true
  await loadProject()
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
