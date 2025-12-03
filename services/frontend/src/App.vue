<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

import Header from './components/layout/Header.vue'
import TaskCard from './components/task-board/TaskCard.vue'
import NewTaskCard from './components/task-board/NewTaskCard.vue'
import CreateTaskModal from './components/task-board/CreateTaskModal.vue'
import WsaWrapper from './components/apps/WsaWrapper.vue' // Импортируем обертку

// --- ТИПЫ ---
interface Task {
  iid: number
  title: string
  description?: string
  formatted_date: string
  calc_type: string     // computed from backend
  turbine_project: string // computed from backend
  labels: string[]
  state: string
  due_date?: string
}

// --- CONSTANTS ---
const TABS = [
  { id: 'all', label: 'Все задачи', tag: null },
  { id: 'valves', label: 'Штоки клапанов', tag: 'valves' },
  { id: 'balance', label: 'Балансы', tag: 'balance' },
  { id: 'triangles', label: 'Треугольники скоростей', tag: 'triangles' },
  { id: 'thermal', label: 'Тепловые расчёты', tag: 'thermal' },
  { id: 'strength', label: 'Прочность', tag: 'strength' },
  { id: 'vibration', label: 'Вибрация', tag: 'vibration' },
]

// --- STATE ---
const currentUser = ref({ name: 'Загрузка...', avatar_url: '' })
const tasks = ref<Task[]>([])
const activeTabId = ref('all')
const showCreateModal = ref(false)
const searchQuery = ref('')
const loading = ref(true)
const sortOrder = ref<'desc' | 'asc'>('desc')

// Управление экранами (Дашборд или Приложение)
const activeView = ref<'dashboard' | 'app-valves'>('dashboard')
const currentTaskIid = ref(0)

// --- API ---
const fetchData = async () => {
  try {
    const [userRes, tasksRes] = await Promise.all([
      axios.get('/api/v1/user/me'),
      axios.get('/api/v1/tasks?state=opened')
    ])
    currentUser.value = userRes.data
    tasks.value = tasksRes.data
  } catch (e) { console.error(e) } 
  finally { loading.value = false }
}

const createTask = async (data: any) => {
  try {
    await axios.post('/api/v1/tasks', {
      title: data.title,
      description: data.description,
      labels: data.labels // [type, project]
    })
    showCreateModal.value = false
    await fetchData()
  } catch (e: any) {
    alert('Ошибка: ' + e.message)
  }
}

const handleTaskClick = (task: Task) => {
  // Логика роутинга: проверяем тип задачи
  // Если это "valves", "Штоки" или заголовок содержит "шток"
  if (task.calc_type === 'valves' || task.labels.includes('valves') || task.title.toLowerCase().includes('шток')) {
    
    if (!confirm(`Открыть приложение "Расчёт штоков" для задачи #${task.iid}?`)) return;
    
    currentTaskIid.value = task.iid
    activeView.value = 'app-valves'
  } else {
    // Для других типов пока заглушка
    alert(`Для типа "${task.calc_type}" интерфейс еще не готов.`)
  }
}

// --- COMPUTED ---
const filteredTasks = computed(() => {
  let result = [...tasks.value]

  // 1. Фильтр по вкладке
  const activeTab = TABS.find(t => t.id === activeTabId.value)
  if (activeTab && activeTab.tag) {
    result = result.filter(t => t.calc_type === activeTab.tag)
  }

  // 2. Поиск
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => t.title.toLowerCase().includes(q) || t.turbine_project.toLowerCase().includes(q))
  }

  // 3. Сортировка
  result.sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return sortOrder.value === 'asc' ? dateA - dateB : dateB - dateA
  })

  return result
})

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

onMounted(fetchData)
</script>

<template>
  <div class="layout">
    
    <!-- ШАПКА (Показываем только на дашборде, т.к. у приложения своя шапка) -->
    <Header v-if="activeView === 'dashboard'" :user="currentUser" />

    <!-- ВАРИАНТ 1: DASHBOARD (Сетка задач) -->
    <main v-if="activeView === 'dashboard'" class="main-container">
      
      <!-- НАВИГАЦИЯ -->
      <nav class="main-nav">
        <a 
          v-for="tab in TABS" 
          :key="tab.id"
          href="#" 
          class="nav-link"
          :class="{ active: activeTabId === tab.id }"
          @click.prevent="activeTabId = tab.id"
        >
          {{ tab.label }}
        </a>
      </nav>

      <!-- ФИЛЬТРЫ -->
      <div class="actions-row">
        <div class="search-input">
          <span class="icon">🔍</span>
          <input v-model="searchQuery" type="text" placeholder="Поиск по названию или проекту..." />
        </div>
        
        <button class="action-btn" @click="alert('Расширенные фильтры скоро будут!')">
           <span class="icon">🌪</span> Фильтрация
        </button>
        
        <button class="action-btn" @click="toggleSort">
           <span class="icon">⇅</span> 
           Сортировка ({{ sortOrder === 'desc' ? 'Новые' : 'Старые' }})
        </button>
        
        <button class="action-btn primary" @click="fetchData">↻ Обновить</button>
      </div>

      <!-- СЕТКА ЗАДАЧ -->
      <div class="task-grid">
        <NewTaskCard @click="showCreateModal = true" />

        <div v-if="loading">Загрузка...</div>
        
        <TaskCard 
          v-for="task in filteredTasks" 
          :key="task.iid" 
          :task="task"
          @click="handleTaskClick(task)"
        />
      </div>
    </main>

    <!-- ВАРИАНТ 2: APP VIEW (Встроенное приложение) -->
    <div v-else-if="activeView === 'app-valves'" style="height: 100vh; width: 100%;">
      <WsaWrapper 
        :taskIid="currentTaskIid" 
        @back="activeView = 'dashboard'" 
      />
    </div>

    <!-- МОДАЛКА СОЗДАНИЯ ЗАДАЧИ -->
    <CreateTaskModal 
      v-if="showCreateModal" 
      @close="showCreateModal = false"
      @create="createTask"
    />

  </div>
</template>

<style>
/* Импорт шрифтов */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
  background-color: #FFFFFF;
  overflow-y: scroll;
}

.layout {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* --- STYLES FOR DASHBOARD --- */

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
  padding: 0 32px;
  border-bottom: 1px solid #E6E6E6;
  background: #fff;
}

.main-container {
  flex: 1;
  padding: 32px;
}

.main-nav {
  display: flex;
  gap: 30px;
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.nav-link {
  text-decoration: none;
  color: #000;
  font-size: 16px;
  white-space: nowrap;
  padding-bottom: 12px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.nav-link:hover { color: #666; }

.nav-link.active {
  font-weight: 600;
  color: #000;
  border-bottom: 2px solid #000;
}

.actions-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.search-input {
  flex-grow: 1;
  display: flex;
  align-items: center;
  padding: 0 12px;
  height: 40px;
  border: 1px solid #D9D9D9;
  border-radius: 4px;
  background: #fff;
  min-width: 200px;
}

.search-input input {
  border: none; outline: none; width: 100%; font-size: 16px; font-family: inherit;
}

.action-btn {
  display: flex; align-items: center; justify-content: center;
  padding: 0 20px; height: 40px; background: #F2F2F2;
  border: none; border-radius: 4px; cursor: pointer;
  font-size: 15px; font-family: inherit; gap: 8px;
  transition: background 0.2s; white-space: nowrap;
}

.action-btn:hover { background: #e0e0e0; }
.action-btn.primary { background: #000; color: #fff; }
.action-btn.primary:hover { background: #333; }

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  padding-bottom: 50px;
}
</style>