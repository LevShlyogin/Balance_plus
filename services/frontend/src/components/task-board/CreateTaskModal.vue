<template>
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content">
        <h2>Создание задачи</h2>
        
        <div class="form-group">
          <label>Название задачи</label>
          <input v-model="form.title" placeholder="Например: Расчет теплообмена" />
        </div>
  
        <div class="form-group">
          <label>Тип расчёта (1-й тег)</label>
          <select v-model="form.type">
            <option value="balance">Балансы</option>
            <option value="valves">Штоки клапанов</option>
            <option value="triangles">Треугольники скоростей</option>
            <option value="thermal">Тепловые расчёты</option>
            <option value="strength">Прочность</option>
            <option value="vibration">Вибрация</option>
          </select>
        </div>
  
        <div class="form-group">
          <label>Проект / Турбина (2-й тег)</label>
          <input v-model="form.project" placeholder="Например: T-100" />
        </div>
  
        <div class="form-group">
          <label>Описание</label>
          <textarea v-model="form.description" rows="3"></textarea>
        </div>
  
        <div class="actions">
          <button @click="$emit('close')" class="btn-cancel">Отмена</button>
          <button @click="submit" class="btn-submit">Создать</button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { reactive } from 'vue'
  
  const emit = defineEmits(['close', 'create'])
  
  const form = reactive({
    title: '',
    type: 'balance',
    project: '',
    description: ''
  })
  
  const submit = () => {
    if (!form.title || !form.project) return alert('Заполните название и проект')
    
    // Формируем массив меток: [Тип, Проект]
    const labels = [form.type, form.project]
    
    emit('create', { ...form, labels })
  }
  </script>
  
  <style scoped>
  .modal-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex; justify-content: center; align-items: center;
    z-index: 1000;
  }
  .modal-content {
    background: white; padding: 30px; border-radius: 8px; width: 500px;
  }
  .form-group { margin-bottom: 15px; }
  .form-group label { display: block; margin-bottom: 5px; font-weight: 500; font-size: 14px;}
  input, select, textarea { 
    width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-family: inherit;
  }
  .actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
  button { padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; }
  .btn-cancel { background: #eee; }
  .btn-submit { background: #000; color: white; }
  </style>