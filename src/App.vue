<script setup lang="ts">
import { ref, computed } from 'vue'
import { invoke } from '@tauri-apps/api/core'

const filePath = ref('')
const fileName = ref('')
const companyName = ref('')
const processing = ref(false)
const statusMessage = ref('')

const ivaModalVisible = ref(false)
const ivaTotal = ref(0)
const ivaChecked = ref(false)
const ivaTempState = ref('')

const outputPath = ref('')
const done = ref(false)

const canSubmit = computed(() => filePath.value && companyName.value.trim())

function handleFileSelect() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.xls,.xlsx'
  input.onchange = (e) => {
    const target = e.target as HTMLInputElement
    if (target.files?.[0]) {
      const file = target.files[0]
      filePath.value = (file as any).path || file.name
      fileName.value = file.name
    }
  }
  input.click()
}

function clearFile() {
  filePath.value = ''
  fileName.value = ''
}

async function startProcessing() {
  if (!canSubmit.value || processing.value) return

  processing.value = true
  done.value = false
  statusMessage.value = 'Reading file...'

  try {
    const result: any = await invoke('process_file', {
      sourcePath: filePath.value,
      companyName: companyName.value.trim(),
    })

    if (result.status === 'iva_question') {
      ivaTotal.value = result.total
      ivaTempState.value = result.temp_state
      ivaChecked.value = false
      ivaModalVisible.value = true
      statusMessage.value = 'IVA confirmation needed'
    } else if (result.status === 'done') {
      outputPath.value = result.output_path
      done.value = true
      statusMessage.value = 'File processed successfully'
    } else {
      statusMessage.value = result.message || 'Processing complete'
      done.value = true
    }
  } catch (err: any) {
    statusMessage.value = `Error: ${err}`
  } finally {
    processing.value = false
  }
}

async function confirmIva() {
  ivaModalVisible.value = false
  processing.value = true
  statusMessage.value = 'Finalizing...'

  try {
    const result: any = await invoke('apply_iva_decision', {
      tempState: ivaTempState.value,
      applyIva: ivaChecked.value,
    })

    outputPath.value = result.output_path
    done.value = true
    statusMessage.value = 'File processed successfully'
  } catch (err: any) {
    statusMessage.value = `Error: ${err}`
  } finally {
    processing.value = false
  }
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="app-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" stroke-width="1.5"/>
          <path d="M8 8h8M8 12h8M8 16h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <h1 class="app-title">xlsFormatter</h1>
      <p class="app-subtitle">Format Excel files for import</p>
    </header>

    <div class="card">
      <div class="form-group">
        <label class="form-label">Source File</label>
        <div
          class="file-zone"
          :class="{ 'file-zone--filled': filePath }"
          @click="handleFileSelect"
          @dragover.prevent
          @drop.prevent=""
        >
          <div v-if="!filePath" class="file-placeholder">
            <svg class="file-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 3v10M6 9l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3 14v2a2 2 0 002 2h10a2 2 0 002-2v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <span>Choose .xls or .xlsx file</span>
          </div>
          <div v-else class="file-selected">
            <svg class="file-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="3" y="1" width="12" height="16" rx="2" stroke="currentColor" stroke-width="1.3"/>
              <path d="M6 7h6M6 10h6M6 13h3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
            <span class="file-name">{{ fileName }}</span>
            <button class="file-clear" @click.stop="clearFile" aria-label="Remove file">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label" for="company">Company Name</label>
        <input
          id="company"
          v-model="companyName"
          type="text"
          class="text-input"
          placeholder="e.g. Acme Corp"
          autocomplete="off"
        />
      </div>

      <button
        class="submit-btn"
        :class="{ 'submit-btn--active': canSubmit }"
        :disabled="!canSubmit || processing"
        @click="startProcessing"
      >
        <span v-if="processing" class="spinner"></span>
        <svg v-else class="btn-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ processing ? 'Processing...' : 'Process File' }}
      </button>
    </div>

    <div v-if="statusMessage" class="status-bar" :class="{ 'status-bar--done': done, 'status-bar--error': statusMessage.startsWith('Error') }">
      <span v-if="done" class="status-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/>
          <path d="M5.5 8l2 2 3-3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </span>
      <span v-else-if="statusMessage.startsWith('Error')" class="status-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/>
          <path d="M6 6l4 4M10 6l-4 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
      </span>
      {{ statusMessage }}
      <span v-if="outputPath" class="status-path">{{ outputPath }}</span>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="ivaModalVisible" class="modal-overlay" @click.self="ivaModalVisible = false">
      <div class="modal-card">
        <div class="modal-header">
          <div class="modal-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.5"/>
              <path d="M10 6v4M10 13v.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <h2 class="modal-title">IVA Confirmation</h2>
        </div>

        <div class="modal-body">
          <div class="total-display">
            <span class="total-label">Total Import</span>
            <span class="total-amount">${{ ivaTotal.toFixed(2) }}</span>
          </div>

          <label class="iva-checkbox">
            <input v-model="ivaChecked" type="checkbox" class="checkbox-input" />
            <span class="checkbox-custom">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2.5 6l2.5 2.5 4.5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <span class="checkbox-label">Apply IVA (21%)</span>
          </label>
        </div>

        <div class="modal-footer">
          <button class="modal-btn modal-btn--secondary" @click="ivaModalVisible = false">
            Cancel
          </button>
          <button class="modal-btn modal-btn--primary" @click="confirmIva">
            Confirm
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.app-container {
  width: 100%;
}

.app-header {
  text-align: center;
  margin-bottom: 28px;
}

.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--accent-soft);
  color: var(--accent);
  margin-bottom: 12px;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.app-subtitle {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 28px 24px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border);
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-of-type {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.file-zone {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 14px;
  border: 1.5px dashed var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition);
  user-select: none;
}

.file-zone:hover {
  border-color: var(--accent);
  background: var(--surface-hover);
}

.file-zone--filled {
  border-style: solid;
  border-color: var(--border);
}

.file-placeholder {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.file-icon {
  flex-shrink: 0;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  color: var(--text-primary);
}

.file-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9rem;
}

.file-clear {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition);
}

.file-clear:hover {
  background: #f0f0f2;
  color: var(--text-secondary);
}

.text-input {
  width: 100%;
  height: 48px;
  padding: 0 14px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: 1rem;
  color: var(--text-primary);
  outline: none;
  transition: all var(--transition);
}

.text-input::placeholder {
  color: var(--text-tertiary);
}

.text-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 48px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  background: #f0f0f2;
  color: var(--text-tertiary);
}

.submit-btn:disabled {
  cursor: not-allowed;
}

.submit-btn--active {
  background: var(--accent);
  color: #fff;
}

.submit-btn--active:hover {
  background: var(--accent-hover);
}

.submit-btn--active:active {
  transform: scale(0.985);
}

.btn-icon {
  flex-shrink: 0;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  font-size: 0.85rem;
  color: var(--text-secondary);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
}

.status-bar--done {
  border-color: var(--success);
  color: #1d8b3a;
}

.status-bar--error {
  border-color: var(--danger);
  color: var(--danger);
}

.status-icon {
  display: flex;
  flex-shrink: 0;
}

.status-path {
  width: 100%;
  font-size: 0.78rem;
  color: var(--text-tertiary);
  word-break: break-all;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  z-index: 100;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  width: 360px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.2s ease;
}

@keyframes slideUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px 0;
}

.modal-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #fff3cd;
  color: #e6a700;
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.modal-body {
  padding: 20px 24px;
}

.total-display {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
}

.total-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.total-amount {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.iva-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.checkbox-custom {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 1.5px solid var(--border);
  border-radius: 5px;
  transition: all var(--transition);
  flex-shrink: 0;
  color: transparent;
}

.checkbox-input:checked + .checkbox-custom {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.checkbox-custom svg {
  opacity: 0;
  transition: opacity var(--transition);
}

.checkbox-input:checked + .checkbox-custom svg {
  opacity: 1;
}

.checkbox-label {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.modal-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 0 24px 20px;
}

.modal-btn {
  padding: 8px 18px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.modal-btn--secondary {
  background: #f0f0f2;
  color: var(--text-secondary);
}

.modal-btn--secondary:hover {
  background: #e5e5e7;
}

.modal-btn--primary {
  background: var(--accent);
  color: #fff;
}

.modal-btn--primary:hover {
  background: var(--accent-hover);
}
</style>
