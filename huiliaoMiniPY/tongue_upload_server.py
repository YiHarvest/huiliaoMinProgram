import cgi
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional

from test_shezheng_api import (
    MAX_POLL_COUNT,
    POLL_INTERVAL_SECONDS,
    resolve_video_path,
    wait_for_health_analysis,
)
from config import config

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_VIDEO_SIZE = 5 * 1024 * 1024


def json_bytes(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode('utf-8')


def save_upload_file(file_item: cgi.FieldStorage, suffix: str) -> Path:
    filename = Path(file_item.filename or f'upload{suffix}').name
    target = UPLOAD_DIR / f"{int(time.time() * 1000)}_{filename}"
    with target.open('wb') as output:
        while True:
            chunk = file_item.file.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    return target


def map_error_message(error_code: Optional[str], fallback: str) -> str:
    if error_code == 'VIDEO_POOR_QUALITY':
        return '视频质量不满足要求，请检查大小、时长、帧率以及是否清晰拍到人脸和舌头'
    if error_code == 'HEALTH_ANALYSIS_ERROR':
        return '分析失败，请稍后重试'
    if error_code == 'HEALTH_ANALYSIS_TIMEOUT':
        return '分析超时，请稍后重试'
    return fallback or '分析失败，请稍后重试'


def build_report_payload(result: dict[str, Any]) -> dict[str, Any]:
    data = result.get('data') or {}
    response = data.get('faceAnalysisResponse') or {}
    assessment = response.get('healthAssessment') or {}
    suggestions = response.get('healthSuggestions') or {}
    tongue = response.get('tongueAnalysis') or {}
    face = response.get('faceAnalysis') or {}
    analysis = response.get('healthAnalysis') or {}

    return {
        'analysisId': data.get('id'),
        'overall': {
            'subject': assessment.get('subject') or '',
            'score': assessment.get('score'),
            'summary': assessment.get('summary') or '',
            'riskWarnings': assessment.get('riskWarnings') or []
        },
        'healthSuggestions': {
            'diet': suggestions.get('diet') or [],
            'exercise': suggestions.get('exercise') or '',
            'physicalTherapy': suggestions.get('physicalTherapy') or ''
        },
        'tongueAnalysis': {
            'summary': tongue.get('summary') or '',
            'tongueColor': tongue.get('tongueColor') or [],
            'tongueShape': tongue.get('tongueShape') or [],
            'coatingTexture': tongue.get('coatingTexture') or [],
            'coatingColor': tongue.get('coatingColor') or []
        },
        'faceAnalysis': {
            'summary': face.get('summary') or '',
            'complexion': face.get('complexion') or [],
            'nose': face.get('nose') or [],
            'shape': face.get('shape') or [],
            'yinTang': face.get('yinTang') or [],
            'lipColor': face.get('lipColor') or [],
            'eyeState': face.get('eyeState') or []
        },
        'healthAnalysis': {
            'subjectName': analysis.get('subjectName') or '',
            'subjectFeature': analysis.get('subjectFeature') or '',
            'subjectOutline': analysis.get('subjectOutline') or '',
            'dietAccept': analysis.get('dietAccept') or '',
            'dietReject': analysis.get('dietReject') or '',
            'exerciseAccept': analysis.get('exerciseAccept') or '',
            'exerciseReject': analysis.get('exerciseReject') or '',
            'physicalPosition': analysis.get('physicalPosition') or '',
            'physicalSearch': analysis.get('physicalSearch') or '',
            'physicalOperation': analysis.get('physicalOperation') or ''
        },
        'basicInfo': {
            'sex': assessment.get('sex') or '',
            'age': assessment.get('age') or ''
        },
        'rawResult': result
    }


class TongueUploadHandler(BaseHTTPRequestHandler):
    server_version = 'TongueUploadProxy/1.0'

    def write_json(self, data: Any, status: int = 200) -> None:
        encoded = json_bytes(data)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self.write_json({})

    def do_GET(self) -> None:
        if self.path == '/health':
            self.write_json({
                'status': 'ok',
                'exampleVideo': '/examples/tongue-video',
                'maxVideoSize': MAX_VIDEO_SIZE,
                'maxPollCount': MAX_POLL_COUNT,
                'pollIntervalSeconds': POLL_INTERVAL_SECONDS,
            })
            return

        if self.path == '/examples/tongue-video':
            video_path = resolve_video_path()
            file_size = video_path.stat().st_size
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Content-Length', str(file_size))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with video_path.open('rb') as source:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            return

        self.write_json({'error': 'Not Found'}, status=404)

    def do_POST(self) -> None:
        if self.path != '/api/tongue-analysis':
            self.write_json({'error': 'Not Found'}, status=404)
            return

        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self.write_json({'error': '请求必须使用 multipart/form-data'}, status=400)
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type
            }
        )

        video_item = form['video'] if 'video' in form else None
        if video_item is None or not getattr(video_item, 'file', None):
            self.write_json({'error': '请上传视频文件'}, status=400)
            return

        video_path = save_upload_file(video_item, '.mp4')

        try:
            if video_path.stat().st_size > MAX_VIDEO_SIZE:
                self.write_json({'error': '视频大小不能超过 5MB'}, status=400)
                return

            response = wait_for_health_analysis(video_path)
            result = response.get('result') or {}
            error_code = result.get('errorCode')

            if response.get('timeout'):
                self.write_json({'error': '分析超时，请稍后重试'}, status=504)
                return

            if result.get('success') is False:
                self.write_json(
                    {
                        'error': map_error_message(error_code, result.get('errorMsg') or ''),
                        'errorCode': error_code,
                        'tips': response.get('tips')
                    },
                    status=502
                )
                return

            report = build_report_payload(result)
            report['analysisId'] = report.get('analysisId') or response.get('analysisId')
            self.write_json(
                {
                    'success': True,
                    'tips': response.get('tips'),
                    'report': report
                }
            )
        except Exception as exc:
            self.write_json({'error': str(exc)}, status=502)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server() -> None:
    host = config['server']['host']
    port = config['server']['port']
    server = ThreadingHTTPServer((host, port), TongueUploadHandler)
    print(f'Tongue upload proxy running on http://{host}:{port}')
    server.serve_forever()


if __name__ == '__main__':
    run_server()