import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    {
      path: '/drama/create',
      name: 'drama-create',
      component: () => import('@/views/drama/ProjectCreate.vue')
    },
    {
      path: '/drama/:id',
      name: 'drama-workspace',
      component: () => import('@/views/drama/ScriptWorkspace.vue')
    },
    {
      path: '/drama/:id/storyboard',
      name: 'drama-storyboard',
      component: () => import('@/views/drama/StoryboardEdit.vue')
    },
    {
      path: '/drama/:id/preview',
      name: 'drama-preview',
      component: () => import('@/views/drama/VideoPreview.vue')
    },
    {
      path: '/video/select',
      name: 'video-select',
      component: () => import('@/views/video/CharacterSelect.vue')
    },
    {
      path: '/video/scene',
      name: 'video-scene',
      component: () => import('@/views/video/SceneConfig.vue')
    },
    {
      path: '/video/result',
      name: 'video-result',
      component: () => import('@/views/video/VideoResult.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/settings/SettingsLayout.vue'),
      children: [
        {
          path: 'models',
          name: 'model-config',
          component: () => import('@/views/settings/ModelConfig.vue')
        },
        {
          path: 'prompts',
          name: 'prompt-templates',
          component: () => import('@/views/settings/PromptTemplates.vue')
        },
        {
          path: 'defaults',
          name: 'default-settings',
          component: () => import('@/views/settings/DefaultSettings.vue')
        }
      ]
    },
    {
      path: '/characters',
      name: 'characters',
      component: () => import('@/views/CharactersView.vue')
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/views/ProjectsView.vue')
    }
  ]
})

export default router
