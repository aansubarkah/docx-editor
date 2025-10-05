import type { Operation } from './types'
import { insertAfterAnchor } from './anchors'

export async function applyOps(ops: Operation[]){
  for(const op of ops){
    if(op.type==='replace_text'){
      await Word.run(async (context) => {
        const hits = context.document.search(op.find || '', { matchCase:false })
        hits.load('items'); await context.sync()
        for(const r of hits.items){ r.insertText(op.replace || '', 'Replace') }
        await context.sync()
      })
    } else if(op.type==='add_heading'){
      const lvl = Math.min(6, Math.max(1, op.level || 1))
      const text = op.text || ''
      await insertAfterAnchor(op.after_paragraph_id || '', (range) => {
        const p = range.insertParagraph(text, Word.InsertLocation.replace)
        ;(p as any).styleBuiltIn = ('heading'+lvl) as any
      })
    } else if(op.type==='add_paragraph'){
      const text = op.text || ''
      await insertAfterAnchor(op.after_paragraph_id || '', (range) => {
        range.insertParagraph(text, Word.InsertLocation.replace)
      })
    } else if(op.type==='insert_table'){
      const rows = op.rows || (op.data ? op.data.length : 2)
      const cols = op.cols || (op.data && op.data[0] ? op.data[0].length : 2)
      await insertAfterAnchor(op.after_paragraph_id || '', (range) => {
        range.insertTable(rows, cols, Word.InsertLocation.replace, op.data as any)
      })
    }
  }
}
