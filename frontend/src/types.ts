export type OpType = "add_heading" | "add_paragraph" | "replace_text" | "insert_table" | "edit_table" | "remove_table" | "remove_paragraph"

export interface Operation {
  type: OpType
  text?: string
  level?: number
  after_paragraph_id?: string
  after_heading_text?: string // legacy fallback
  find?: string
  replace?: string
  rows?: number
  cols?: number
  data?: string[][]
  table_index?: number // for edit_table (0-based index)
  cell_row?: number // for edit_table cell editing
  cell_col?: number // for edit_table cell editing
  cell_text?: string // for edit_table cell editing
  add_header_row?: boolean // for insert_table styling
}

export interface OutlineItem {
  paragraph_id: string
  text: string
  level: number // 0 for body, 1..6 for headings
}
