<template>
  <div class="max-w-4xl mx-auto">
    <header class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">提示词模板</h1>
        <p class="text-on-surface-variant">管理您的自定义提示词模板</p>
      </div>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors flex items-center gap-2"
      >
        <span class="material-symbols-outlined text-sm">add</span>
        新建模板
      </button>
    </header>

    <!-- Template List -->
    <div class="bg-surface-container-lowest rounded-lg overflow-hidden">
      <table class="w-full">
        <thead class="bg-surface-container-low">
          <tr>
            <th class="text-left p-4 text-xs font-bold uppercase tracking-wider text-on-surface-variant">模板名称</th>
            <th class="text-left p-4 text-xs font-bold uppercase tracking-wider text-on-surface-variant">类型</th>
            <th class="text-right p-4 text-xs font-bold uppercase tracking-wider text-on-surface-variant">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="template in templates" :key="template.id" class="border-t border-surface-container">
            <td class="p-4">
              <span class="font-medium">{{ template.name }}</span>
              <span v-if="template.is_system" class="ml-2 text-xs bg-surface-container px-2 py-0.5 rounded">系统</span>
            </td>
            <td class="p-4 text-on-surface-variant text-sm">
              {{ getTypeLabel(template.type) }}
            </td>
            <td class="p-4 text-right">
              <button
                @click="editTemplate(template)"
                class="px-3 py-1 text-sm text-primary hover:bg-primary/10 rounded transition-colors"
              >
                编辑
              </button>
              <button
                v-if="!template.is_system"
                @click="deleteTemplate(template.id)"
                class="px-3 py-1 text-sm text-error hover:bg-error/10 rounded transition-colors"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { promptTemplateApi } from '@/api/promptTemplate'

const templates = ref([])
const showCreateModal = ref(false)

const typeLabels = {
  script: '剧本生成',
  character: '角色生成',
  storyboard: '分镜生成',
  video: '视频生成'
}

const getTypeLabel = (type) => typeLabels[type] || type

const loadTemplates = async () => {
  try {
    const response = await promptTemplateApi.getAll()
    templates.value = response.data
  } catch (error) {
    console.error('Failed to load templates:', error)
  }
}

const editTemplate = (template) => {
  // Open edit modal
  console.log('Edit:', template)
}

const deleteTemplate = async (id) => {
  if (confirm('确定要删除此模板吗？')) {
    try {
      await promptTemplateApi.delete(id)
      loadTemplates()
    } catch (error) {
      alert('删除失败')
    }
  }
}

onMounted(loadTemplates)
</script>
