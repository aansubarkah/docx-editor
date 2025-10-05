import os, json, uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from models import PlanOpsRequest, ApplyOpsRequest, CreateDocRequest, Operation, OutlineItem
from doc_ops import create_document, apply_operations, build_outline, load_outline, redline_compare, list_versions, load_doc
from preview import convert_docx_to_html
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")  # Optional: for custom endpoints
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

app = FastAPI(title="Docx Agent MVP v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(BASE_DIR, "..", "storage"))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")

os.makedirs(STORAGE_DIR, exist_ok=True)

# Serve built frontend (Vite build outputs to dist/)
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

def _file_path(file_id: str) -> str:
    return os.path.join(STORAGE_DIR, f"{file_id}.docx")

@app.post("/api/create")
async def create_doc(req: CreateDocRequest):
    fid = create_document(req.title, req.body)
    return {"file_id": fid, "download_url": f"/api/download/{fid}"}

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Upload a .docx")
    fid = str(uuid.uuid4())
    path = _file_path(fid)
    with open(path, "wb") as f:
        f.write(await file.read())
    # initial outline and first version
    from doc_ops import save_version, build_outline
    build_outline(fid)  # also persisted in save_version path during create? ensure outline exists
    save_version(fid, path)
    return {"file_id": fid, "download_url": f"/api/download/{fid}"}

@app.get("/api/download/{file_id}")
async def download(file_id: str):
    path = _file_path(file_id)
    if not os.path.exists(path): raise HTTPException(404, "Not found")
    return FileResponse(path, filename=f"{file_id}.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.get("/api/preview/{file_id}")
async def preview_html(file_id: str):
    """Convert docx to HTML with proper numbering support"""
    try:
        doc = load_doc(file_id)
        html_content = convert_docx_to_html(doc)
        return JSONResponse({"html": html_content})
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/outline/{file_id}")
async def outline(file_id: str):
    try:
        outline = load_outline(file_id)
        return [o.__dict__ for o in outline]
    except Exception as e:
        raise HTTPException(404, str(e))

@app.get("/api/versions/{file_id}")
async def versions(file_id: str):
    return {"versions": list_versions(file_id)}

@app.get("/api/redline")
async def redline(base_id: str, revised_id: str):
    try:
        out_id = redline_compare(base_id, revised_id)
        return {"file_id": out_id, "download_url": f"/api/download/{out_id}"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/plan-ops")
async def plan_ops(req: PlanOpsRequest):
    instruction = req.instruction.strip()

    if not OPENAI_API_KEY:
        # Heuristic: basic "replace 'A' with 'B'"; add H2 after paragraph anchor like pid(h2:...)
        ops = []
        m = re.search(r"replace\s+'(.+?)'\s+with\s+'(.+?)'", instruction, re.I)
        if m:
            ops.append({"type":"replace_text","find":m.group(1),"replace":m.group(2)})
        else:
            ops.append({"type":"add_paragraph","text":f"(Note) {instruction}"})
        return {"operations": ops, "note":"Set OPENAI_API_KEY for full planning."}

    try:
        from openai import OpenAI

        # Initialize client with optional base_url for custom endpoints
        client_kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL

        client = OpenAI(**client_kwargs)
        tool_schema = {
            "type":"function",
            "function":{
                "name":"propose_operations",
                "description":"Propose a list of precise .docx operations. Prefer using after_paragraph_id anchors from the outline.",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "operations":{
                            "type":"array",
                            "items":{
                                "type":"object",
                                "properties":{
                                    "type":{"type":"string","enum":["add_heading","add_paragraph","replace_text","insert_table","edit_table","remove_table","remove_paragraph"]},
                                    "text":{"type":"string"},
                                    "level":{"type":"integer","minimum":1,"maximum":6},
                                    "after_paragraph_id":{"type":"string"},
                                    "find":{"type":"string"},
                                    "replace":{"type":"string"},
                                    "rows":{"type":"integer","minimum":1},
                                    "cols":{"type":"integer","minimum":1},
                                    "data":{"type":"array","items":{"type":"array","items":{"type":"string"}}},
                                    "table_index":{"type":"integer","minimum":0,"description":"Index of table to edit (0-based)"},
                                    "cell_row":{"type":"integer","minimum":0,"description":"Row index of cell to edit"},
                                    "cell_col":{"type":"integer","minimum":0,"description":"Column index of cell to edit"},
                                    "cell_text":{"type":"string","description":"New text for the cell"},
                                    "add_header_row":{"type":"boolean","description":"Style first row as header"}
                                },
                                "required":["type"]
                            }
                        }
                    },
                    "required":["operations"]
                }
            }
        }
        outline_json = []
        if req.file_id:
            try:
                outline_json = [o for o in (await outline(req.file_id))]  # reuse handler (sync call in same process is fine)
            except Exception:
                pass

        system = """You are a careful docx editor. Return only operations via the tool. Use after_paragraph_id anchors when inserting.

IMPORTANT for converting content to tables:

A) Paragraph to table conversion:
1. Use insert_table with after_paragraph_id to place table AFTER the paragraph
2. Use remove_paragraph with after_paragraph_id to remove the original paragraph

B) Numbered/bulleted list to table conversion:
1. Identify ALL list items to convert (they will have sequential paragraph_ids)
2. Use insert_table with after_paragraph_id set to the LAST list item's ID
3. Use multiple remove_paragraph operations to remove EACH list item by its paragraph_id
4. Parse list content intelligently:
   - For "Name: Value" format → 2 columns
   - For simple lists → 1 column
   - Extract data from list markers (1., 2., 3., •, etc.)

C) Converting ranges:
- Always insert the table AFTER the last item to be converted
- Remove all items being converted using their individual paragraph_ids
- This ensures correct positioning

Example for "convert these 3 numbered items to a table":
[
  {"type": "insert_table", "after_paragraph_id": "p-item3", "rows": 3, "cols": 2, "data": [...]},
  {"type": "remove_paragraph", "after_paragraph_id": "p-item1"},
  {"type": "remove_paragraph", "after_paragraph_id": "p-item2"},
  {"type": "remove_paragraph", "after_paragraph_id": "p-item3"}
]"""
        user_msg = "Instruction: " + instruction + "\nOutline: " + json.dumps(outline_json)

        operations = None

        # Try with function/tool calling first
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role":"system","content":system},
                    {"role":"user","content":user_msg}
                ],
                tools=[tool_schema],
                tool_choice={"type":"function","function":{"name":"propose_operations"}}
            )

            # Extract tool call from response
            if resp.choices and resp.choices[0].message.tool_calls:
                tool_call = resp.choices[0].message.tool_calls[0]
                arguments = json.loads(tool_call.function.arguments)
                operations = arguments.get("operations")

        except Exception as tool_error:
            # Fallback for providers without tool calling support
            print(f"Tool calling failed, trying JSON mode fallback: {tool_error}")

            # Try JSON mode or plain response
            fallback_system = """You are a docx editor. Parse the user's instruction and return ONLY a valid JSON object with this structure:
{
  "operations": [
    {"type": "replace_text", "find": "old", "replace": "new"},
    {"type": "add_paragraph", "text": "content", "after_paragraph_id": "p-xxx"},
    {"type": "add_heading", "text": "heading", "level": 2},
    {"type": "insert_table", "rows": 2, "cols": 3, "data": [["a","b","c"],["d","e","f"]]}
  ]
}
Return ONLY valid JSON, no other text."""

            try:
                resp = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role":"system","content":fallback_system},
                        {"role":"user","content":user_msg}
                    ],
                    temperature=0
                )

                # Parse JSON from response
                response_text = resp.choices[0].message.content.strip()
                # Try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                result = json.loads(response_text)
                operations = result.get("operations", [])
            except Exception as fallback_error:
                print(f"JSON fallback also failed: {fallback_error}")

        if not operations:
            return {"operations": [], "note": "Model did not return operations. Try again."}
        return {"operations": operations}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in plan-ops: {error_detail}")
        return JSONResponse({"operations": [], "error": str(e), "detail": error_detail}, status_code=500)

@app.post("/api/apply-ops")
async def apply_ops(req: ApplyOpsRequest):
    from doc_ops import apply_operations
    new_id, outline = apply_operations(req.file_id, [Operation(**op) if isinstance(op, dict) else op for op in req.operations])
    return {"file_id": new_id, "download_url": f"/api/download/{new_id}", "outline": [o.__dict__ for o in outline]}
