"""
Enhanced DOCX to HTML converter with numbering support
"""
from docx import Document
from docx.oxml.ns import qn
from typing import Dict, List
import html


class DocxToHtmlConverter:
    def __init__(self, doc: Document):
        self.doc = doc
        self.numbering_dict = self._parse_numbering()
        self.list_counters = {}  # Track current counter for each list level

    def _parse_numbering(self) -> Dict:
        """Parse numbering definitions from the document"""
        numbering_dict = {}
        try:
            numbering_part = self.doc.part.numbering_part
            if numbering_part is None:
                return {}

            # Parse abstract numbering definitions
            for abstractNum in numbering_part.element.findall('.//' + qn('w:abstractNum')):
                abstractNumId = abstractNum.get(qn('w:abstractNumId'))
                levels = {}

                for lvl in abstractNum.findall('.//' + qn('w:lvl')):
                    ilvl = lvl.get(qn('w:ilvl'))
                    numFmt = lvl.find('.//' + qn('w:numFmt'))
                    lvlText = lvl.find('.//' + qn('w:lvlText'))

                    fmt = numFmt.get(qn('w:val')) if numFmt is not None else 'decimal'
                    text = lvlText.get(qn('w:val')) if lvlText is not None else '%1.'

                    levels[ilvl] = {'format': fmt, 'text': text}

                numbering_dict[abstractNumId] = levels

            # Map num IDs to abstract num IDs
            for num in numbering_part.element.findall('.//' + qn('w:num')):
                numId = num.get(qn('w:numId'))
                abstractNumId_elem = num.find('.//' + qn('w:abstractNumId'))
                if abstractNumId_elem is not None:
                    abstractNumId = abstractNumId_elem.get(qn('w:val'))
                    if abstractNumId in numbering_dict:
                        numbering_dict[numId] = numbering_dict[abstractNumId]

        except Exception as e:
            print(f"Error parsing numbering: {e}")

        return numbering_dict

    def _get_numbering_info(self, paragraph):
        """Extract numbering information from a paragraph"""
        try:
            pPr = paragraph._element.find(qn('w:pPr'))
            if pPr is None:
                return None

            numPr = pPr.find(qn('w:numPr'))
            if numPr is None:
                return None

            ilvl_elem = numPr.find(qn('w:ilvl'))
            numId_elem = numPr.find(qn('w:numId'))

            if ilvl_elem is None or numId_elem is None:
                return None

            ilvl = ilvl_elem.get(qn('w:val'))
            numId = numId_elem.get(qn('w:val'))

            if numId in self.numbering_dict and ilvl in self.numbering_dict[numId]:
                return {
                    'numId': numId,
                    'ilvl': int(ilvl),
                    'format': self.numbering_dict[numId][ilvl]['format'],
                    'text': self.numbering_dict[numId][ilvl]['text']
                }

        except Exception as e:
            print(f"Error getting numbering info: {e}")

        return None

    def _format_number(self, counter: int, fmt: str) -> str:
        """Format a counter based on numbering format"""
        if fmt == 'decimal':
            return str(counter)
        elif fmt == 'upperRoman':
            return self._to_roman(counter).upper()
        elif fmt == 'lowerRoman':
            return self._to_roman(counter).lower()
        elif fmt == 'upperLetter':
            return chr(64 + counter)  # A, B, C...
        elif fmt == 'lowerLetter':
            return chr(96 + counter)  # a, b, c...
        elif fmt == 'bullet':
            return '•'
        else:
            return str(counter)

    def _to_roman(self, num: int) -> str:
        """Convert number to Roman numerals"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        result = ''
        for i in range(len(val)):
            count = int(num / val[i])
            if count:
                result += syms[i] * count
                num -= val[i] * count
        return result

    def _get_paragraph_style(self, paragraph) -> str:
        """Get the style name of a paragraph"""
        try:
            return paragraph.style.name
        except:
            return 'Normal'

    def convert_to_html(self) -> str:
        """Convert document to HTML with numbering"""
        html_parts = []

        for para in self.doc.paragraphs:
            # Check if paragraph is numbered
            num_info = self._get_numbering_info(para)

            # Get paragraph text
            text = html.escape(para.text)

            # Determine paragraph style
            style_name = self._get_paragraph_style(para)

            if num_info:
                # Handle numbered/bulleted lists
                ilvl = num_info['ilvl']
                numId = num_info['numId']
                fmt = num_info['format']

                # Track counter for this list level
                key = f"{numId}_{ilvl}"
                if key not in self.list_counters:
                    self.list_counters[key] = 1
                else:
                    self.list_counters[key] += 1

                counter = self.list_counters[key]

                # Format the number/bullet
                if fmt == 'bullet':
                    marker = '•'
                    list_type = 'ul'
                else:
                    marker = self._format_number(counter, fmt) + '.'
                    list_type = 'ol'

                # Add list item with proper indentation
                indent = ilvl * 30
                html_parts.append(
                    f'<div class="list-item" style="margin-left: {indent}px;">'
                    f'<span class="list-marker">{marker}</span> {text}'
                    f'</div>'
                )

            elif 'Heading' in style_name:
                # Handle headings
                level = 1
                try:
                    level = int(style_name.split()[-1])
                except:
                    level = 1
                html_parts.append(f'<h{level}>{text}</h{level}>')

            else:
                # Regular paragraph
                if text.strip():
                    html_parts.append(f'<p>{text}</p>')
                else:
                    html_parts.append('<p>&nbsp;</p>')

        # Handle tables
        for table in self.doc.tables:
            html_parts.append('<table>')
            for row in table.rows:
                html_parts.append('<tr>')
                for cell in row.cells:
                    cell_text = html.escape(cell.text)
                    html_parts.append(f'<td>{cell_text}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')

        return '\n'.join(html_parts)


def convert_docx_to_html(doc: Document) -> str:
    """Main function to convert DOCX to HTML with numbering"""
    converter = DocxToHtmlConverter(doc)
    return converter.convert_to_html()
