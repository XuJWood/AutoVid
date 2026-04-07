<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold font-headline tracking-tight">分镜编辑</h1>
          <p class="text-sm text-on-surface-variant mt-1">管理每个镜头的图像和视频</p>
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
            @click="generateStoryboard"
            :disabled="generating"
            class="flex items-center gap-2 bg-primary-container text-on-primary-container px-4 py-2 rounded-full text-sm font-bold hover:brightness-95 transition-all disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-sm">auto_awesome</span>
            {{ generating ? '生成中...' : '生成分镜' }}
          </button>
          <router-link
            v-if="storyboards.length > 0"
            :to="`/drama/${projectId}/preview`"
            class="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-full text-sm font-bold hover:brightness-95 transition-all"
          >
            <span class="material-symbols-outlined text-sm">play_arrow</span>
            预览视频
          </router-link>
        </div>
      </div>

      <!-- Stats Bar -->
      <div v-if="storyboards.length > 0" class="bg-surface-container-low rounded-lg p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">movie</span>
              <span class="text-sm"><strong>{{ storyboards.length }}</strong> 个分镜</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-green-600">image</span>
              <span class="text-sm"><strong>{{ completedImages }}</strong> / {{ storyboards.length }} 图片</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-600">videocam</span>
              <span class="text-sm"><strong>{{ completedVideos }}</strong> / {{ storyboards.length }} 视频</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateAllImages"
              :disabled="generatingAll || !hasPendingImages"
              class="px-3 py-1.5 text-xs font-bold bg-green-100 text-green-800 rounded-full hover:bg-green-200 transition-colors disabled:opacity-50"
            >
              批量生成图片
            </button>
            <button
              @click="generateAllVideos"
              :disabled="generatingAll || !hasPendingVideos"
              class="px-3 py-1.5 text-xs font-bold bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors disabled:opacity-50"
            >
              批量生成视频
            </button>
          </div>
        </div>
      </div>

      <!-- Generation Progress -->
      <div v-if="generating" class="bg-primary/10 rounded-lg p-6 mb-6">
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

      <!-- Storyboard Grid -->
      <div v-if="groupedStoryboards.length > 0" class="space-y-8">
        <div v-for="group in groupedStoryboards" :key="group.sceneIndex" class="bg-surface-container-lowest rounded-lg p-6 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">scene</span>
              场景 {{ group.sceneIndex + 1 }}
            </h3>
            <span class="text-xs text-on-surface-variant">{{ group.shots.length }} 个镜头</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            <div
              v-for="shot in group.shots"
              :key="shot.id"
              class="bg-surface-container-low rounded-lg overflow-hidden border border-surface-container"
            >
              <!-- Preview Area -->
              <div class="aspect-video bg-surface-container relative">
                <img
                  v-if="shot.image_url"
                  :src="shot.image_url"
                  class="w-full h-full object-cover"
                />
                <video
                  v-else-if="shot.video_url"
                  :src="shot.video_url"
                  class="w-full h-full object-cover"
                  muted
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="material-symbols-outlined text-4xl text-on-surface-variant opacity-50">image</span>
                </div>

                <!-- Status Badge -->
                <div class="absolute top-2 right-2">
                  <span
                    v-if="shot.status === 'completed'"
                    class="px-2 py-1 text-xs font-bold bg-green-500 text-white rounded-full"
                  >
                    完成
                  </span>
                  <span
                    v-else-if="shot.status === 'processing'"
                    class="px-2 py-1 text-xs font-bold bg-yellow-500 text-white rounded-full"
                  >
                    生成中
                  </span>
                  <span
                    v-else-if="shot.status === 'failed'"
                    class="px-2 py-1 text-xs font-bold bg-red-500 text-white rounded-full"
                  >
                    失败
                  </span>
                </div>

                <!-- Duration Badge -->
                <div class="absolute bottom-2 right-2 bg-black/60 text-white px-2 py-0.5 rounded text-xs font-bold">
                  {{ shot.duration }}s
                </div>
              </div>

              <!-- Info -->
              <div class="p-3">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                    {{ shot.shot_type || '镜头' }} {{ shot.shot_index + 1 }}
                  </span>
                </div>
                <p class="text-xs text-on-surface-variant line-clamp-2 mb-3">{{ shot.description }}</p>

                <!-- Actions -->
                <div class="flex gap-2">
                  <button
                    @click="generateImage(shot)"
                    :disabled="shot.status === 'processing'"
                    class="flex-1 py-1.5 text-xs font-bold bg-green-100 text-green-800 rounded hover:bg-green-200 transition-colors disabled:opacity-50"
                  >
                    {{ shot.image_url ? '重新生成图片' : '生成图片' }}
                  </button>
                  <button
                    @click="generateVideo(shot)"
                    :disabled="shot.status === 'processing' || !shot.image_url"
                    class="flex-1 py-1.5 text-xs font-bold bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors disabled:opacity-50"
                  >
                    {{ shot.video_url ? '重新生成视频' : '生成视频' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-surface-container-lowest rounded-lg p-12 text-center">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-50 mb-4">movie_filter</span>
        <h3 class="text-lg font-bold mb-2">还没有分镜数据</h3>
        <p class="text-sm text-on-surface-variant mb-4">请先生成剧本，然后点击"生成分镜"按钮</p>
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
const storyboards = ref([])
const generating = ref(false)
const generatingAll = ref(false)
const progress = ref(0)
const progressMessage = ref('')

// Computed
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

const completedImages = computed(() => {
  return storyboards.value.filter(sb => sb.image_url).length
})

const completedVideos = computed(() => {
  return storyboards.value.filter(sb => sb.video_url).length
})

const hasPendingImages = computed(() => {
  return storyboards.value.some(sb => !sb.image_url && sb.status !== 'processing')
})

const hasPendingVideos = computed(() => {
  return storyboards.value.some(sb => sb.image_url && !sb.video_url && sb.status !== 'processing')
})

// Methods
const loadProject = async () => {
  try {
    const res = await projectsApi.get(projectId)
    project.value = res.data
  } catch (error) {
    console.error('Failed to load project:', error)
  }
}

const loadStoryboards = async () => {
  try {
    const res = await storyboardApi.getByProject(projectId)
    storyboards.value = res.data
  } catch (error) {
    console.error('Failed to load storyboards:', error)
  }
}

const generateStoryboard = async () => {
  generating.value = true
  progress.value = 0
  progressMessage.value = '正在从剧本生成分镜...'

  try {
    await storyboardApi.generate(projectId)
    progress.value = 100
    progressMessage.value = '分镜生成成功！'
    await loadStoryboards()
  } catch (error) {
    console.error('Failed to generate storyboard:', error)
    progressMessage.value = '生成失败：' + (error.response?.data?.detail || error.message)
  } finally {
    setTimeout(() => {
      generating.value = false
    }, 1000)
  }
}

const generateImage = async (shot) => {
  const originalStatus = shot.status
  shot.status = 'processing'

  try {
    const res = await storyboardApi.generateImage(shot.id)
    if (res.data.status === 'completed') {
      shot.image_url = res.data.image_url
      shot.status = 'completed'
    } else {
      shot.status = 'failed'
    }
  } catch (error) {
    console.error('Failed to generate image:', error)
    shot.status = 'failed'
  }
}

const generateVideo = async (shot) => {
  const originalStatus = shot.status
  shot.status = 'processing'

  try {
    const res = await storyboardApi.generateVideo(shot.id)
    if (res.data.status === 'completed') {
      shot.video_url = res.data.video_url
      shot.status = 'completed'
    } else {
      shot.status = 'failed'
    }
  } catch (error) {
    console.error('Failed to generate video:', error)
    shot.status = 'failed'
  }
}

const generateAllImages = async () => {
  generatingAll.value = true
  const pendingShots = storyboards.value.filter(sb => !sb.image_url && sb.status !== 'processing')

  for (const shot of pendingShots) {
    await generateImage(shot)
  }

  generatingAll.value = false
}

const generateAllVideos = async () => {
  generatingAll.value = true
  const pendingShots = storyboards.value.filter(sb => sb.image_url && !sb.video_url && sb.status !== 'processing')

  for (const shot of pendingShots) {
    await generateVideo(shot)
  }

  generatingAll.value = false
}

onMounted(async () => {
  await loadProject()
  await loadStoryboards()
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
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
