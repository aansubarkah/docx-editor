<template>
  <div class="h-screen flex flex-col" :class="isDarkMode ? 'bg-gray-900' : 'bg-gray-50'">
    <!-- Header -->
    <header class="px-6 py-4 flex items-center justify-between border-b" :class="isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'">
      <div class="flex items-center gap-3">
        <h1 class="text-xl font-bold" :class="isDarkMode ? 'text-white' : 'text-gray-900'">📝 Docx Agent</h1>
        <span class="text-sm" :class="isDarkMode ? 'text-gray-400' : 'text-gray-500'">AI-powered document editor</span>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="isDarkMode = !isDarkMode"
          class="px-3 py-2 text-sm rounded-lg transition-colors"
          :class="isDarkMode ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'"
        >
          {{ isDarkMode ? '☀️ Light' : '🌙 Dark' }}
        </button>
        <input
          type="file"
          accept=".docx"
          @change="onUpload"
          ref="fileInput"
          class="hidden"
        />
        <button
          @click="$refs.fileInput.click()"
          class="px-4 py-2 text-sm rounded-lg border transition-colors"
          :class="isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
        >
          📁 Upload .docx
        </button>
        <button
          @click="createNewDoc"
          class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          ✨ New Document
        </button>
      </div>
    </header>

    <!-- Main Content: Two Columns -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Column: Chat Interface -->
      <div class="w-1/2 flex flex-col border-r" :class="isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'">
        <!-- Chat Messages -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
            <div class="text-center text-gray-400">
              <p class="text-lg mb-2">💬 Start a conversation</p>
              <p class="text-sm">Tell me what you'd like to do with your document</p>
            </div>
          </div>

          <div v-for="(msg, idx) in messages" :key="idx" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
            <div
              class="max-w-[80%] rounded-lg px-4 py-2"
              :class="msg.role === 'user' ? 'bg-blue-600 text-white' : (isDarkMode ? 'bg-gray-700 text-gray-100' : 'bg-gray-100 text-gray-900')"
            >
              <div v-if="msg.role === 'assistant' && msg.operations" class="space-y-2">
                <p class="text-sm font-medium mb-2">{{ msg.text }}</p>
                <details class="text-xs">
                  <summary class="cursor-pointer opacity-75 hover:opacity-100">View operations JSON</summary>
                  <pre class="mt-2 p-2 bg-gray-800 text-green-400 rounded overflow-auto">{{ JSON.stringify(msg.operations, null, 2) }}</pre>
                </details>
                <button
                  @click="applyOperations(msg.operations)"
                  class="mt-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                >
                  ✅ Apply Changes
                </button>
              </div>
              <p v-else class="text-sm">{{ msg.text }}</p>
            </div>
          </div>

          <div v-if="isLoading" class="flex justify-start">
            <div class="rounded-lg px-4 py-2" :class="isDarkMode ? 'bg-gray-700 text-gray-100' : 'bg-gray-100 text-gray-900'">
              <div class="flex items-center gap-2">
                <div class="animate-spin h-4 w-4 border-2 border-t-transparent rounded-full" :class="isDarkMode ? 'border-gray-400' : 'border-gray-600'"></div>
                <span class="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="border-t p-4" :class="isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'">
          <div class="flex gap-2">
            <input
              v-model="userInput"
              @keydown.enter="sendMessage"
              type="text"
              placeholder="e.g., Add a heading 'Introduction' or replace 'foo' with 'bar'..."
              class="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              :class="isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'"
            />
            <button
              @click="sendMessage"
              :disabled="!userInput.trim() || isLoading"
              class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
          <div v-if="fileId" class="mt-2 flex items-center gap-2 text-xs" :class="isDarkMode ? 'text-gray-400' : 'text-gray-500'">
            <span>📄 Active document:</span>
            <code class="bg-gray-200 px-2 py-1 rounded">{{ fileId.substring(0, 8) }}...</code>
            <a :href="downloadUrl" class="text-blue-600 hover:underline" target="_blank">Download</a>
          </div>
        </div>
      </div>

      <!-- Right Column: Document Preview -->
      <div class="w-1/2 flex flex-col" :class="isDarkMode ? 'bg-gray-800' : 'bg-white'">
        <!-- Preview Header -->
        <div class="border-b px-6 py-3 flex items-center justify-between" :class="isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'">
          <h2 class="font-semibold" :class="isDarkMode ? 'text-white' : 'text-gray-900'">Document Preview</h2>
          <div class="flex items-center gap-2">
            <select
              v-model="previewMode"
              @change="refreshPreview"
              class="px-2 py-1 text-sm border rounded transition-colors"
              :class="isDarkMode ? 'bg-gray-600 border-gray-500 text-white' : 'bg-white border-gray-300 text-gray-900'"
              :disabled="!fileId"
            >
              <option value="mammoth">HTML Preview</option>
              <option value="office">Office Viewer</option>
            </select>
            <button
              @click="refreshPreview"
              class="px-3 py-1 text-sm border rounded transition-colors"
              :class="isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-600' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
              :disabled="!fileId"
            >
              🔄 Refresh
            </button>
            <button
              @click="showOutline = !showOutline"
              class="px-3 py-1 text-sm border rounded transition-colors"
              :class="isDarkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-600' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
              :disabled="!fileId"
            >
              {{ showOutline ? '📄 Preview' : '📋 Outline' }}
            </button>
          </div>
        </div>

        <!-- Preview Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <div v-if="!fileId" class="h-full flex items-center justify-center text-gray-400">
            <div class="text-center">
              <p class="text-lg mb-2">📄 No document loaded</p>
              <p class="text-sm">Create a new document or upload an existing one</p>
            </div>
          </div>

          <!-- Outline View -->
          <div v-else-if="showOutline" class="space-y-2">
            <div
              v-for="item in outline"
              :key="item.paragraph_id"
              class="group p-2 rounded cursor-pointer transition-colors"
              :class="isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'"
              @click="copyParagraphId(item.paragraph_id)"
            >
              <div class="flex items-start gap-3">
                <div
                  class="text-xs mt-1"
                  :class="isDarkMode ? 'text-gray-500' : 'text-gray-400'"
                  :style="{ marginLeft: (item.level * 16) + 'px' }"
                >
                  {{ item.level > 0 ? `H${item.level}` : '¶' }}
                </div>
                <div class="flex-1 min-w-0">
                  <code class="text-xs text-blue-500 opacity-0 group-hover:opacity-100">{{ item.paragraph_id }}</code>
                  <p class="text-sm truncate" :class="isDarkMode ? 'text-gray-300' : 'text-gray-700'">{{ item.text || '(empty)' }}</p>
                </div>
              </div>
            </div>
            <p class="text-xs mt-4" :class="isDarkMode ? 'text-gray-500' : 'text-gray-400'">💡 Click any paragraph to copy its ID for precise insertion</p>
          </div>

          <!-- Document Preview -->
          <div v-else class="h-full">
            <!-- Office Online Viewer -->
            <iframe
              v-if="previewMode === 'office' && downloadUrl"
              :src="`https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(window.location.origin + downloadUrl)}`"
              class="w-full h-full border-0"
              frameborder="0"
            ></iframe>

            <!-- Mammoth HTML Preview -->
            <div v-else-if="previewMode === 'mammoth'" :class="isDarkMode ? 'bg-gray-700' : 'bg-gray-100'">
              <div v-if="previewHtml" v-html="previewHtml" class="docx-preview max-w-none" :class="isDarkMode ? 'dark-mode' : ''"></div>
              <div v-else class="text-center text-gray-400">
                <p>Loading preview...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from "vue"
import type { Operation, OutlineItem } from "./types"
import mammoth from "mammoth"

interface Message {
  role: 'user' | 'assistant'
  text: string
  operations?: Operation[]
}

const fileId = ref<string>("")
const downloadUrl = ref<string>("")
const userInput = ref<string>("")
const messages = ref<Message[]>([])
const isLoading = ref(false)
const outline = ref<OutlineItem[]>([])
const previewHtml = ref<string>("")
const showOutline = ref(false)
const previewMode = ref<'mammoth' | 'office'>('mammoth')
const isDarkMode = ref(true) // Default to dark mode

const backend = ""

async function createNewDoc() {
  const title = prompt("Document title:", "New Document")
  if (!title) return

  const res = await fetch(backend + "/api/create", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({title, body: ""})
  })
  const data = await res.json()
  fileId.value = data.file_id
  downloadUrl.value = data.download_url

  await refreshOutline()
  await refreshPreview()

  messages.value.push({
    role: 'assistant',
    text: `Created new document: "${title}"`
  })
}

async function onUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const fd = new FormData()
  fd.append("file", file)
  const res = await fetch(backend + "/api/upload", { method:"POST", body: fd })
  const data = await res.json()
  fileId.value = data.file_id
  downloadUrl.value = data.download_url

  await refreshOutline()
  await refreshPreview()

  messages.value.push({
    role: 'assistant',
    text: `Uploaded document: ${file.name}`
  })
}

async function sendMessage() {
  if (!userInput.value.trim() || isLoading.value) return

  const instruction = userInput.value
  messages.value.push({
    role: 'user',
    text: instruction
  })
  userInput.value = ""
  isLoading.value = true

  try {
    const res = await fetch(backend + "/api/plan-ops", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ file_id: fileId.value || null, instruction })
    })
    const data = await res.json()

    if (data.operations && data.operations.length > 0) {
      messages.value.push({
        role: 'assistant',
        text: `I've planned ${data.operations.length} operation(s) for you:`,
        operations: data.operations
      })
    } else {
      messages.value.push({
        role: 'assistant',
        text: data.note || "I couldn't generate operations for that instruction. Please try rephrasing."
      })
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      text: "Sorry, I encountered an error processing your request."
    })
  } finally {
    isLoading.value = false
  }
}

async function applyOperations(operations: Operation[]) {
  if (!fileId.value) return

  isLoading.value = true
  try {
    const res = await fetch(backend + "/api/apply-ops", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ file_id: fileId.value, operations })
    })
    const data = await res.json()
    downloadUrl.value = data.download_url

    await refreshOutline(data.outline)
    await refreshPreview()

    messages.value.push({
      role: 'assistant',
      text: "✅ Changes applied successfully!"
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      text: "❌ Failed to apply changes."
    })
  } finally {
    isLoading.value = false
  }
}

async function refreshOutline(pre?: OutlineItem[]) {
  if (pre) {
    outline.value = pre
    return
  }
  if (!fileId.value) return

  const res = await fetch(backend + "/api/outline/" + fileId.value)
  outline.value = await res.json()
}

async function refreshPreview() {
  if (!fileId.value) return

  if (previewMode.value === 'office') {
    // Office viewer doesn't need processing
    return
  }

  try {
    // Use custom backend endpoint with numbering support
    const res = await fetch(backend + "/api/preview/" + fileId.value)
    const data = await res.json()
    previewHtml.value = data.html
  } catch (error) {
    console.error("Preview error:", error)
    previewHtml.value = "<p class='text-red-500'>Failed to load preview</p>"
  }
}

function copyParagraphId(id: string) {
  navigator.clipboard.writeText(id)
  messages.value.push({
    role: 'assistant',
    text: `📋 Copied paragraph ID: ${id}\n\nYou can now reference this in your instructions, e.g., "insert paragraph after ${id}"`
  })
}

watch(fileId, () => {
  if (fileId.value) {
    refreshPreview()
  }
})
</script>

<style>
/* Word-like document styling */
.docx-preview {
  @apply text-gray-900;
  font-family: 'Calibri', 'Arial', sans-serif;
  font-size: 11pt;
  line-height: 1.5;
  max-width: 8.5in;
  margin: 0 auto;
  padding: 1in;
  background: white;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  min-height: 11in;
}

.docx-preview h1 {
  font-size: 20pt;
  font-weight: bold;
  margin-top: 24pt;
  margin-bottom: 12pt;
  color: #1a1a1a;
}

.docx-preview h2 {
  font-size: 16pt;
  font-weight: bold;
  margin-top: 18pt;
  margin-bottom: 10pt;
  color: #1a1a1a;
}

.docx-preview h3 {
  font-size: 14pt;
  font-weight: bold;
  margin-top: 14pt;
  margin-bottom: 8pt;
  color: #1a1a1a;
}

.docx-preview h4 {
  font-size: 12pt;
  font-weight: bold;
  margin-top: 12pt;
  margin-bottom: 6pt;
  color: #1a1a1a;
}

.docx-preview p {
  margin-bottom: 10pt;
  text-align: left;
}

.docx-preview table {
  border-collapse: collapse;
  margin: 12pt 0;
  width: 100%;
  font-size: 11pt;
}

.docx-preview td, .docx-preview th {
  border: 1px solid #000;
  padding: 4pt 8pt;
  text-align: left;
  vertical-align: top;
}

.docx-preview th {
  background-color: #f0f0f0;
  font-weight: bold;
}

.docx-preview ul, .docx-preview ol {
  margin: 6pt 0;
  padding-left: 36pt;
}

.docx-preview li {
  margin-bottom: 6pt;
}

.docx-preview strong {
  font-weight: bold;
}

.docx-preview em {
  font-style: italic;
}

.docx-preview u {
  text-decoration: underline;
}

/* Page break simulation */
.docx-preview .page-break {
  page-break-before: always;
  border-top: 1px dashed #ccc;
  margin: 1in 0;
  padding-top: 1in;
}

/* Numbered/Bulleted Lists */
.docx-preview .list-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 6pt;
  line-height: 1.5;
}

.docx-preview .list-marker {
  min-width: 30px;
  display: inline-block;
  font-weight: normal;
  margin-right: 8px;
  flex-shrink: 0;
}

/* Nested list indentation is handled inline via style attribute */

/* Dark mode for document preview */
.docx-preview.dark-mode {
  background: #1f2937;
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
}

.docx-preview.dark-mode h1,
.docx-preview.dark-mode h2,
.docx-preview.dark-mode h3,
.docx-preview.dark-mode h4 {
  color: #f3f4f6;
}

.docx-preview.dark-mode p {
  color: #e5e7eb;
}

.docx-preview.dark-mode table {
  border-color: #4b5563;
}

.docx-preview.dark-mode td,
.docx-preview.dark-mode th {
  border-color: #4b5563;
  color: #e5e7eb;
}

.docx-preview.dark-mode th {
  background-color: #374151;
}

.docx-preview.dark-mode .list-item {
  color: #e5e7eb;
}

.docx-preview.dark-mode .list-marker {
  color: #9ca3af;
}
</style>
