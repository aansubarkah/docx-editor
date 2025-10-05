export type OpType = 'add_heading' | 'add_paragraph' | 'replace_text' | 'insert_table'
export interface Operation {
  type: OpType
  text?: string
  level?: number
  after_paragraph_id?: string
  find?: string
  replace?: string
  rows?: number
  cols?: number
  data?: string[][]
}
export interface OutlineItem { paragraph_id: string; text: string; level: number }
