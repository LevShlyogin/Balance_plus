<template>
    <div class="iframe-container">
      <div v-if="saving" class="overlay">
        <div class="loader">💾 Сохранение результатов в GitLab...</div>
      </div>
  
      <!-- Встраиваем внешний фронтенд -->
      <!-- Передаем taskId и флаг embedded, чтобы тот фронт знал, что он внутри IDE -->
      <iframe 
        ref="iframeRef"
        :src="iframeSrc" 
        class="app-frame"
        frameborder="0"
      ></iframe>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import axios from 'axios'
  
  const props = defineProps<{ taskIid: number }>()
  const emit = defineEmits(['back'])
  
  const saving = ref(false)
  // Адрес вашего существующего фронта
  const EXTERNAL_APP_URL = 'http://10.202.220.143:5252' 
  
  const iframeSrc = computed(() => {
    // Добавляем параметры, чтобы внешний фронт понял контекст
    return `${EXTERNAL_APP_URL}?taskId=${props.taskIid}&embedded=true`
  })
  
  // Обработчик сообщений от Iframe
  const handleMessage = async (event: MessageEvent) => {
    // Проверка безопасности: принимаем сообщения только от нашего приложения
    // if (event.origin !== 'http://10.202.220.143:5252') return; 
    
    const { type, payload } = event.data
  
    if (type === 'WSA_CALCULATION_COMPLETE') {
      await saveResult(payload)
    }
    
    if (type === 'WSA_CLOSE') {
      emit('back')
    }
  }
  
  const saveResult = async (data: any) => {
    saving.value = true
    try {
      // Отправляем в наш Оркестратор
      const requestPayload = {
        task_iid: props.taskIid,
        app_type: 'valves', // Имя папки в Git
        input_data: data.input,
        output_data: data.output,
        commit_message: `Расчёт из внешнего приложения`
      }
  
      const res = await axios.post('/api/v1/calculations/save', requestPayload)
      
      // Сообщаем Iframe, что всё ок (опционально)
      alert(`✅ Результаты сохранены в задачу #${props.taskIid}!`)
    } catch (e: any) {
      alert('Ошибка сохранения: ' + e.message)
    } finally {
      saving.value = false
    }
  }
  
  onMounted(() => {
    window.addEventListener('message', handleMessage)
  })
  
  onUnmounted(() => {
    window.removeEventListener('message', handleMessage)
  })
  </script>
  
  <style scoped>
  .iframe-container { width: 100%; height: 100%; position: relative; }
  .app-frame { width: 100%; height: 100%; display: block; }
  .overlay { 
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
    background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center;
    font-size: 20px; font-weight: bold; z-index: 10;
  }
  </style>