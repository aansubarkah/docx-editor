<template>
  <div class="w-[360px] p-4 space-y-4 text-gray-900">
    <h1 class="text-xl font-bold">Docx Agent (Sideload)</h1>
    <div class="space-y-2">
      <label class="text-sm font-medium">OpenAI API Key (optional)</label>
      <input v-model="apiKey" type="password" class="w-full border rounded px-2 py-1" placeholder="sk-..." />
      <p class="text-xs text-gray-500">Stored in localStorage. Leave empty for heuristic planning.</p>
    </div>
    <div class="space-y-2">
      <label class="text-sm font-medium">Instruction</label>
      <textarea v-model="instruction" rows="4" class="w-full border rounded px-2 py-1" placeholder="After anchor h2-xxxx, add a 2x3 table..."></textarea>
      <div class="flex gap-2">
        <button @click="plan" class="px-3 py-2 rounded bg-gray-900 text-white">Plan</button>
        <button @click="apply" :disabled="ops.length===0" class="px-3 py-2 rounded bg-brand text-white disabled:opacity-50">Apply</button>
      </div>
    </div>
    <div>
      <div class="text-sm font-medium mb-1">Planned ops</div>
      <pre class="text-xs bg-gray-100 rounded p-2 overflow-auto h-32">{{ JSON.stringify(ops, null, 2) }}</pre>
    </div>
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <div class="text-sm font-medium">Outline (anchors)</div>
        <button @click="refreshOutline" class="text-sm underline text-brand">Refresh</button>
      </div>
      <div class="border rounded p-2 h-40 overflow-auto space-y-1">
        <div v-for="o in outline" :key="o.paragraph_id" class="text-xs">
          <button class="underline text-brand" @click="copy(o.paragraph_id)">{{ o.paragraph_id }}</button>
          <span class="text-gray-500 ml-2">{{ o.text }}</span>
        </div>
      </div>
      <p class="text-xs text-gray-500">Click an ID to copy; use it as <code>after_paragraph_id</code>.</p>
    </div>
    <div class="space-y-2">
      <div class="text-sm font-medium">Compare (desktop only)</div>
      <div class="flex gap-2">
        <button @click="snapshot" class="px-3 py-2 rounded border">Snapshot base</button>
        <button @click="compare" class="px-3 py-2 rounded border">Compare vs snapshot</button>
      </div>
      <p class="text-xs text-gray-500">If compare is unsupported, no action will occur.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import './styles.css'
import type { Operation } from './types'
import { applyOps } from './ops-executor'
import { buildOutline } from './anchors'

const apiKey = ref<string>(localStorage.getItem('OPENAI_API_KEY') || '')
const instruction = ref<string>('replace "Foo Ltd" with "Bar LLC"')
const ops = ref<Operation[]>([])
const outline = ref<any[]>([])
const base64Snapshot = ref<string>('')

onMounted(async () => {
  await new Promise<void>(resolve => Office.onReady(() => resolve()))
  await refreshOutline()
})

async function refreshOutline(){ try { outline.value = await buildOutline() } catch(e){ console.error(e) } }

async function plan(){
  if(apiKey.value){
    localStorage.setItem('OPENAI_API_KEY', apiKey.value)
    const sys = 'Return JSON operations only. Use after_paragraph_id anchors when inserting.'
    const user = instruction.value
    try {
      const resp = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer '+apiKey.value, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [
            { role: 'system', content: sys },
            { role: 'user', content: 'Instruction: '+user+'\nReturn JSON array of operations with fields: type,text,level,after_paragraph_id,find,replace,rows,cols,data.' }
          ],
          temperature: 0
        })
      })
      const json = await resp.json()
      const text = json.choices?.[0]?.message?.content || '[]'
      const maybe = JSON.parse(text)
      ops.value = Array.isArray(maybe) ? maybe : []
    } catch(e){ console.error(e); ops.value=[{ type:'add_paragraph', text:'(Note) '+instruction.value }] }
  } else {
    const m = instruction.value.match(/replace\s+"(.+?)"\s+with\s+"(.+?)"/i)
    if(m){ ops.value=[{ type:'replace_text', find:m[1], replace:m[2] }] }
    else { ops.value=[{ type:'add_paragraph', text:'(Note) '+instruction.value }] }
  }
}

async function apply(){ await applyOps(ops.value); await refreshOutline() }
function copy(t: string){ navigator.clipboard.writeText(t) }

async function snapshot(){
  Office.context.document.getFileAsync(Office.FileType.Compressed, { sliceSize: 65536 }, (res) => {
    if(res.status !== Office.AsyncResultStatus.Succeeded) return
    const file = res.value; const slices: string[] = []; let i = 0
    function next(){ file.getSliceAsync(i, (r) => {
      if(r.status !== Office.AsyncResultStatus.Succeeded) return
      slices.push(r.value.data); i++; if(i<file.sliceCount) next(); else { file.closeAsync(); base64Snapshot.value = slices.join('') }
    })}
    next()
  })
}

async function compare(){
  try {
    if(!base64Snapshot.value) return
    await Word.run(async (context) => {
      const app: any = context.application
      if(typeof app.compareFromBase64 !== 'function') return
      Office.context.document.getFileAsync(Office.FileType.Compressed, { sliceSize: 65536 }, (res) => {
        if(res.status !== Office.AsyncResultStatus.Succeeded) return
        const file = res.value; const slices: string[] = []; let i = 0
        function next(){ file.getSliceAsync(i, (r) => {
          if(r.status !== Office.AsyncResultStatus.Succeeded) return
          slices.push(r.value.data); i++; if(i<file.sliceCount) next(); else { file.closeAsync(); app.compareFromBase64(base64Snapshot.value, slices.join(''), 'DocxAgent Compare') }
        })}
        next()
      })
    })
  } catch(e){ console.error(e) }
}
</script>
