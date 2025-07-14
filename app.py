from flask import Flask, render_template, request, jsonify, Response
import requests
import json

app = Flask(__name__)

API_URL = "http://localhost/v1"
API_KEY = "app-Nfqyj2jlcOMxNKFhOnekv9tr"  # 请根据实际情况调整
WORKFLOW_ID = "C3DkottL68M7X1Ic"         # 请根据实际情况调整
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
            "workflow_id": WORKFLOW_ID,
            "inputs": {"input_data": input_data},
            "response_mode": "streaming",
            "user": USER_ID
        }
        # --- SSE流式转发 ---
        def generate():
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
                    # 直接返回错误JSON
                    yield f"data: {{\"error\": \"workflow执行失败\", \"detail\": {json.dumps(resp2.text)}, \"status_code\": {resp2.status_code}, \"headers\": {json.dumps(dict(resp2.headers))}}}\n\n"
                    return
                for line in resp2.iter_lines():
                    if line:
                        yield line + b'\n'
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        # 可选：生产环境可记录日志
        return "Internal Server Error: " + str(e), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8888)