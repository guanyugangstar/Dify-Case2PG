from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import psycopg2

app = Flask(__name__)

API_URL = "http://localhost/v1"
API_KEY = "app-Nfqyj2jlcOMxNKFhOnekv9tr"  # 请根据实际情况调整
USER_ID = "abc-123"                      # 可自定义

# 文件类型映射
EXT_TYPE_MAP = {
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'text/plain': 'txt',
    'text/markdown': 'markdown',
    'text/html': 'html',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-powerpoint': 'ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'application/xml': 'xml',
    'application/epub+zip': 'epub',
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'image/svg+xml': 'svg',
    'audio/mpeg': 'mp3',
    'audio/mp4': 'm4a',
    'audio/wav': 'wav',
    'audio/webm': 'webm',
    'audio/amr': 'amr',
    'video/mp4': 'mp4',
    'video/quicktime': 'mov',
    'video/mpeg': 'mpeg',
    'audio/mpga': 'mpga',
}

# Dify FileType 映射（官方五选一）
EXT_FILETYPE_MAP = {
    # 文档
    'pdf': 'document', 'doc': 'document', 'docx': 'document', 'txt': 'document', 'md': 'document', 'markdown': 'document', 'html': 'document',
    'xls': 'document', 'xlsx': 'document', 'ppt': 'document', 'pptx': 'document', 'xml': 'document', 'epub': 'document',
    'csv': 'document', 'eml': 'document', 'msg': 'document',
    # 图片
    'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image', 'svg': 'image',
    # 音频
    'mp3': 'audio', 'm4a': 'audio', 'wav': 'audio', 'webm': 'audio', 'amr': 'audio', 'mpga': 'audio',
    # 视频
    'mp4': 'video', 'mov': 'video', 'mpeg': 'video',
}

last_workflow_outputs = []  # 临时存储最近一次dify工作流完整输出

# 数据库连接参数（请根据实际情况调整）
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': '123456',
    'dbname': 'postgres'
}

def query_table(table_name, limit=100):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM {table_name} LIMIT %s', (limit,))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {'columns': columns, 'rows': rows}
    except Exception as e:
        return {'error': str(e)}

def guess_type(file):
    mime = file.mimetype
    ext = EXT_TYPE_MAP.get(mime)
    if not ext:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    # 只返回官方五选一
    return EXT_FILETYPE_MAP.get(ext, 'custom')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        files = request.files.getlist("input_data")
        upload_file_ids = []
        file_types = []
        for f in files:
            # Step 1: 上传到 /v1/files/upload
            resp = requests.post(
                f"{API_URL}/files/upload",
                headers={"Authorization": f"Bearer {API_KEY}"},
                files={"file": (f.filename, f.stream, f.mimetype)},
                data={"user": USER_ID}
            )
            if resp.status_code not in (200, 201):
                return jsonify({"error": "文件上传失败", "detail": resp.text, "status_code": resp.status_code, "headers": dict(resp.headers)}), 400
            if not resp.text.strip():
                return jsonify({"error": "文件上传响应为空", "status_code": resp.status_code, "headers": dict(resp.headers)}), 400
            try:
                file_info = json.loads(resp.content.decode('utf-8-sig').strip())
            except Exception as e1:
                return jsonify({
                    "error": "文件上传响应无法解析为JSON",
                    "detail": resp.text,
                    "repr": repr(resp.text),
                    "exception": str(e1),
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers)
                }), 400
            upload_file_ids.append(file_info["id"])
            file_types.append(guess_type(f))
        # Step 2: 调用 /v1/workflows/run
        input_data = [
            {
                "transfer_method": "local_file",
                "upload_file_id": fid,
                "type": ftype
            }
            for fid, ftype in zip(upload_file_ids, file_types)
        ]
        payload = {
            "inputs": {"input_data": input_data},
            "response_mode": "streaming",
            "user": USER_ID
        }
        # --- SSE流式转发 ---
        def generate():
            global last_workflow_outputs
            last_workflow_outputs = []  # 每次新上传清空
            with requests.post(
                f"{API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                stream=True
            ) as resp2:
                if resp2.status_code != 200:
                    yield f"data: {{\"error\": \"workflow执行失败\", \"detail\": {json.dumps(resp2.text)}, \"status_code\": {resp2.status_code}, \"headers\": {json.dumps(dict(resp2.headers))}}}\n\n"
                    return
                for line in resp2.iter_lines():
                    if line:
                        try:
                            # 只处理以data:开头的SSE行
                            if line.startswith(b'data:'):
                                json_str = line[5:].decode('utf-8').strip()
                                obj = json.loads(json_str)
                                last_workflow_outputs.append(obj)
                        except Exception:
                            pass  # 忽略解析失败
                        yield line + b'\n'
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        # 可选：生产环境可记录日志
        return "Internal Server Error: " + str(e), 500

@app.route("/get_table_data", methods=["GET"])
def get_table_data():
    global last_workflow_outputs
    if not last_workflow_outputs:
        return jsonify({'error': '暂无工作流输出，请先上传并处理文件'}), 400
    # 遍历所有json体，查找event为node_finished且data.title为“问题分类器”的节点
    classifier_node = None
    for obj in last_workflow_outputs:
        if isinstance(obj, dict) and obj.get('event') == 'node_finished':
            data = obj.get('data', {})
            if data.get('title') == '问题分类器':
                classifier_node = data
                break
    if not classifier_node:
        return jsonify({'error': '未找到“问题分类器”节点'}), 400
    outputs = classifier_node.get('outputs')
    class_name = None
    if outputs and isinstance(outputs, dict):
        class_name = outputs.get('class_name')
    if not class_name:
        return jsonify({'error': '“问题分类器”节点缺少class_name', 'outputs': outputs}), 400
    table_map = {
        '合同': 'contract_summary',
        '复议': 'reconsideration_summary',
        '诉讼': 'case_summary'
    }
    table = table_map.get(class_name)
    if not table:
        return jsonify({'error': f'class_name为{class_name}，无对应表格'}), 400
    result = query_table(table)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8888)
