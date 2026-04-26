<template>
  <div class="min-h-screen pt-24 pb-32 px-8 flex items-center justify-center">
    <div class="text-center">
      <span class="material-symbols-outlined text-8xl text-on-surface-variant opacity-30 mb-4">error</span>
      <h1 class="text-3xl font-bold font-headline mb-2">页面未找到</h1>
      <p class="text-on-surface-variant mb-6">你访问的页面不存在</p>
      <router-link
        to="/"
        class="inline-flex items-center gap-2 bg-primary text-on-primary px-6 py-3 rounded-full text-sm font-bold hover:brightness-95 transition-all"
      >
        <span class="material-symbols-outlined text-sm">home</span>
        返回首页
      </router-link>
    </div>
  </div>
</template>
