<template>
  <div class="fixed bottom-8 w-full flex justify-center z-50">
    <nav class="rounded-full px-6 py-3 bg-white/80 backdrop-blur-2xl border border-on-surface-variant/10 shadow-lg shadow-primary/10 flex justify-around items-center gap-4">
      <button class="text-on-surface-variant px-4 py-2 flex items-center gap-2 hover:bg-surface-container-low transition-all rounded-full font-bold text-xs">
        <span class="material-symbols-outlined">auto_awesome</span>
        <span>生成剧本</span>
      </button>
      <button class="text-on-surface-variant px-4 py-2 flex items-center gap-2 hover:bg-surface-container-low transition-all rounded-full font-bold text-xs">
        <span class="material-symbols-outlined">magic_button</span>
        <span>AI 优化</span>
      </button>
      <button class="bg-primary text-white rounded-full px-6 py-2 flex items-center gap-2 scale-105 active:scale-95 duration-300 font-bold text-xs shadow-lg shadow-primary/30">
        <span>下一步</span>
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </nav>
  </div>
</template>
