<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-7xl mx-auto">
    <header class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">我的项目</h1>
        <p class="text-on-surface-variant">管理您的所有创作项目</p>
      </div>
      <router-link
        to="/drama/create"
        class="px-4 py-2 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors flex items-center gap-2"
      >
        <span class="material-symbols-outlined text-sm">add</span>
        新建项目
      </router-link>
    </header>

    <!-- Filters -->
    <div class="flex gap-4 mb-8">
      <select v-model="filterType" class="bg-surface-container-lowest border-none rounded-lg px-4 py-2 text-sm">
        <option value="">全部类型</option>
        <option value="drama">短剧创作</option>
        <option value="video">视频生成</option>
      </select>
      <select v-model="filterStatus" class="bg-surface-container-lowest border-none rounded-lg px-4 py-2 text-sm">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="in_progress">进行中</option>
        <option value="completed">已完成</option>
      </select>
    </div>

    <!-- Project Grid -->
    <div v-if="filteredProjects.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div
        v-for="project in filteredProjects"
        :key="project.id"
        class="bg-surface-container-lowest rounded-lg overflow-hidden hover:shadow-lg transition-all group relative"
      >
        <!-- Delete button (top-right, shows on hover) -->
        <button
          @click.stop="confirmDeleteProject(project)"
          :disabled="deletingId === project.id"
          class="absolute top-2 right-2 z-10 w-8 h-8 rounded-full bg-black/60 text-white opacity-0 group-hover:opacity-100 hover:bg-error transition-all flex items-center justify-center disabled:opacity-50"
          title="删除项目"
        >
          <span class="material-symbols-outlined text-base">{{ deletingId === project.id ? 'autorenew' : 'delete' }}</span>
        </button>

        <div @click="openProject(project)" class="cursor-pointer">
          <div class="aspect-video bg-surface-container relative overflow-hidden">
            <img
              v-if="getCover(project.id)"
              :src="getCover(project.id)"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <span class="material-symbols-outlined text-5xl text-on-surface-variant/20">{{ project.type === 'drama' ? 'theater_comedy' : 'videocam' }}</span>
            </div>
            <span class="absolute top-2 left-2 text-xs font-bold px-2 py-1 rounded-full"
              :class="project.type === 'drama' ? 'bg-primary/20 text-primary' : 'bg-tertiary/20 text-tertiary'">
              {{ project.type === 'drama' ? '短剧' : '视频' }}
            </span>
            <span class="absolute bottom-2 right-2 text-xs font-bold px-2 py-1 rounded-full"
              :class="getStatusClass(project.status)">
              {{ getStatusLabel(project.status) }}
            </span>
          </div>
          <div class="p-4">
            <h3 class="font-bold mb-1 truncate">{{ project.name }}</h3>
            <p class="text-xs text-on-surface-variant mb-3 line-clamp-2">{{ project.description || '暂无描述' }}</p>
            <div class="flex justify-between items-center">
              <span class="text-xs text-on-surface-variant">{{ formatDate(project.updated_at) }}</span>
              <div class="flex items-center gap-2">
                <span class="text-xs text-on-surface-variant">{{ getProgressLabel(project) }}</span>
                <div class="h-1 w-16 bg-surface-container rounded-full overflow-hidden">
                  <div class="h-full bg-primary transition-all" :style="{ width: getProgress(project) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Dialog -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8" @click.self="deleteTarget = null">
      <div class="bg-surface-container-lowest rounded-lg max-w-md w-full p-6 shadow-2xl">
        <div class="flex items-start gap-3 mb-4">
          <div class="p-2 bg-error/10 rounded-lg">
            <span class="material-symbols-outlined text-error">warning</span>
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-lg mb-1">确认删除项目</h3>
            <p class="text-sm text-on-surface-variant">即将删除 <strong class="text-on-surface">"{{ deleteTarget.name }}"</strong> 及其所有数据：</p>
          </div>
        </div>
        <ul class="text-xs text-on-surface-variant bg-surface-container-low rounded-lg p-3 mb-4 space-y-1">
          <li class="flex items-center gap-1.5"><span class="material-symbols-outlined text-sm">person</span>所有角色及其形象图</li>
          <li class="flex items-center gap-1.5"><span class="material-symbols-outlined text-sm">movie</span>所有剧集封面、片段视频</li>
          <li class="flex items-center gap-1.5"><span class="material-symbols-outlined text-sm">folder_delete</span>媒体文件夹（无法恢复）</li>
        </ul>
        <div class="flex justify-end gap-2">
          <button @click="deleteTarget = null" class="px-4 py-2 text-sm font-bold rounded-full bg-surface-container hover:bg-surface-container-high transition-colors">
            取消
          </button>
          <button
            @click="executeDelete"
            :disabled="deletingId !== null"
            class="px-4 py-2 text-sm font-bold rounded-full bg-error text-white hover:brightness-110 transition-all disabled:opacity-50"
          >
            {{ deletingId !== null ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-16">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant mb-4">folder_open</span>
      <p class="text-lg text-on-surface-variant mb-4">还没有项目</p>
      <router-link
        to="/drama/create"
        class="px-6 py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors"
      >
        创建第一个项目
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { storyboardApi } from '@/api/storyboard'

const router = useRouter()
const projects = ref([])
const covers = ref({})
const filterType = ref('')
const filterStatus = ref('')
const deleteTarget = ref(null)
const deletingId = ref(null)

const filteredProjects = computed(() => {
  let result = projects.value
  if (filterType.value) {
    result = result.filter(p => p.type === filterType.value)
  }
  if (filterStatus.value) {
    result = result.filter(p => p.status === filterStatus.value)
  }
  return result
})

const statusLabels = {
  draft: '草稿',
  in_progress: '进行中',
  completed: '已完成'
}

const statusClasses = {
  draft: 'bg-surface-container text-on-surface-variant',
  in_progress: 'bg-secondary/20 text-secondary',
  completed: 'bg-primary/20 text-primary'
}

const getStatusLabel = (status) => statusLabels[status] || status
const getStatusClass = (status) => statusClasses[status] || ''

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const getCover = (projectId) => {
  const url = covers.value[projectId]
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

const getProgress = (project) => {
  if (project.status === 'completed') return 100
  if (project.status === 'in_progress') {
    const epCount = covers.value[`${project.id}_count`] || 0
    if (epCount > 0) return Math.min(80, 20 + epCount * 10)
    if (project.script_content && Object.keys(project.script_content).length > 0) return 40
    return 20
  }
  return 0
}

const getProgressLabel = (project) => {
  if (project.status === 'completed') return '已完成'
  if (project.status === 'in_progress') return '制作中'
  return '草稿'
}

const openProject = (project) => {
  if (project.type === 'drama') {
    router.push(`/drama/${project.id}`)
  } else {
    router.push('/video/select')
  }
}

const loadProjects = async () => {
  try {
    const response = await projectsApi.getAll()
    projects.value = response.data
    // 并行获取各项目的剧集封面
    const coverResults = await Promise.allSettled(
      response.data.map(p => storyboardApi.getByProject(p.id).then(r => ({ id: p.id, data: r.data })).catch(() => null))
    )
    const map = {}
    for (const r of coverResults) {
      if (r.status === 'fulfilled' && r.value) {
        const eps = r.value.data || []
        map[`${r.value.id}_count`] = eps.length
        const withCover = eps.find(e => e.image_url)
        if (withCover) map[r.value.id] = withCover.image_url
      }
    }
    covers.value = map
  } catch (error) {
    console.error('Failed to load projects:', error)
  }
}

const confirmDeleteProject = (project) => {
  deleteTarget.value = project
}

const executeDelete = async () => {
  if (!deleteTarget.value) return
  const id = deleteTarget.value.id
  deletingId.value = id
  try {
    await projectsApi.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
    deleteTarget.value = null
  } catch (error) {
    console.error('Failed to delete project:', error)
    alert('删除失败：' + (error.response?.data?.detail || error.message))
  } finally {
    deletingId.value = null
  }
}

onMounted(loadProjects)
</script>
