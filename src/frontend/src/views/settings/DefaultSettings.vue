<template>
  <div class="max-w-2xl mx-auto">
    <header class="mb-8">
      <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">默认设置</h1>
      <p class="text-on-surface-variant">配置系统的默认参数</p>
    </header>

    <div class="space-y-8">
      <!-- Video Defaults -->
      <section class="bg-surface-container-lowest p-8 rounded-lg">
        <h2 class="text-lg font-bold mb-6 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">videocam</span>
          视频默认参数
        </h2>
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <label class="text-sm font-medium">默认时长</label>
            <select v-model="defaults.videoDuration" class="bg-surface-container-low border-none rounded-lg px-4 py-2 text-sm">
              <option value="5">5秒</option>
              <option value="10">10秒</option>
              <option value="15">15秒</option>
            </select>
          </div>
          <div class="flex justify-between items-center">
            <label class="text-sm font-medium">默认比例</label>
            <select v-model="defaults.videoAspectRatio" class="bg-surface-container-low border-none rounded-lg px-4 py-2 text-sm">
              <option value="16:9">16:9 横屏</option>
              <option value="9:16">9:16 竖屏</option>
              <option value="1:1">1:1 方形</option>
            </select>
          </div>
          <div class="flex justify-between items-center">
            <label class="text-sm font-medium">默认分辨率</label>
            <select v-model="defaults.videoResolution" class="bg-surface-container-low border-none rounded-lg px-4 py-2 text-sm">
              <option value="720p">720P</option>
              <option value="1080p">1080P HD</option>
              <option value="4k">4K Ultra</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Publish Defaults -->
      <section class="bg-surface-container-lowest p-8 rounded-lg">
        <h2 class="text-lg font-bold mb-6 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">share</span>
          发布默认设置
        </h2>
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <label class="text-sm font-medium">默认平台</label>
            <select v-model="defaults.publishPlatform" class="bg-surface-container-low border-none rounded-lg px-4 py-2 text-sm">
              <option value="douyin">抖音</option>
              <option value="kuaishou">快手</option>
              <option value="bilibili">B站</option>
            </select>
          </div>
          <div class="flex justify-between items-center">
            <label class="text-sm font-medium">发布间隔</label>
            <select v-model="defaults.publishInterval" class="bg-surface-container-low border-none rounded-lg px-4 py-2 text-sm">
              <option value="0">立即发布</option>
              <option value="30">30分钟</option>
              <option value="60">1小时</option>
              <option value="120">2小时</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Save Button -->
      <button
        @click="saveDefaults"
        class="w-full py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors"
      >
        保存设置
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const defaults = ref({
  videoDuration: '5',
  videoAspectRatio: '16:9',
  videoResolution: '1080p',
  publishPlatform: 'douyin',
  publishInterval: '0'
})

const saveDefaults = () => {
  // Save to localStorage or API
  localStorage.setItem('defaults', JSON.stringify(defaults.value))
  alert('设置已保存')
}
</script>
