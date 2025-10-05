import type { OutlineItem } from './types'

function normalize(s: string){ return (s||'').trim().replace(/\s+/g,' ') }
function hash(s: string){ let h=0; for(let i=0;i<s.length;i++){ h=((h<<5)-h)+s.charCodeAt(i); h|=0 } return (h>>>0).toString(16).slice(0,8) }
function lvlFromStyle(name?: string): number {
  const n=(name||'').toLowerCase()
  if(n.includes('heading 1')) return 1
  if(n.includes('heading 2')) return 2
  if(n.includes('heading 3')) return 3
  if(n.includes('heading 4')) return 4
  if(n.includes('heading 5')) return 5
  if(n.includes('heading 6')) return 6
  return 0
}

export async function buildOutline(): Promise<OutlineItem[]> {
  return Word.run(async (context) => {
    const paras = context.document.body.paragraphs
    paras.load('items/text,items/style,items/styleBuiltIn')
    await context.sync()
    const out: OutlineItem[] = []
    for (let i=0;i<paras.items.length;i++){
      const p = paras.items[i] as any
      const text = normalize(p.text || '')
      const lvl  = lvlFromStyle(p.styleBuiltIn || p.style || '')
      const pid  = (lvl>0?'h'+lvl:'p') + '-' + hash(text + '|' + lvl + '|' + i)
      out.push({ paragraph_id: pid, text, level: lvl })

      // anchor via content control tag
      const r = paras.items[i].getRange()
      const ccs = r.contentControls; ccs.load('items/tag'); await context.sync()
      let has=false; for(const cc of ccs.items){ if(cc.tag===pid){ has=true; break } }
      if(!has){ const cc = r.insertContentControl(); cc.tag = pid; cc.title = 'anchor:'+pid }
    }
    await context.sync()
    Office.context.document.settings.set('anchorOutline', out)
    Office.context.document.settings.saveAsync()
    return out
  })
}

export async function insertAfterAnchor(anchorId: string, insert: (range: Word.Range)=>void){
  return Word.run(async (context) => {
    const ccs = context.document.contentControls.getByTag(anchorId)
    ccs.load('items')
    await context.sync()
    if(ccs.items.length===0) throw new Error('Anchor not found: '+anchorId)
    const r = ccs.items[0].getRange()
    const newRange = r.insertParagraph('', Word.InsertLocation.after).getRange()
    insert(newRange)
    await context.sync()
  })
}
