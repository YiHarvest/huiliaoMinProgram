"""
舌面分析接口测试脚本。

注意：签名与调用逻辑以当前脚本已跑通的实现为准，
如果文档描述存在差异，应优先复用这里的行为。
"""

import hashlib
import hmac
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from config import config


BASE_URL = config['life_emergence']['base_url']
AK = config['life_emergence']['ak']
SK = config['life_emergence']['sk']

START_PATH = "/smyx-open-api/open/health-analysis/v1/start-face-analysis"
QUERY_PATH = "/smyx-open-api/open/health-analysis/v1/query-face-analysis-json"
VIDEO_PATH = Path(r"D:\huiliao\小程序接口\舌诊接口\test_vedio.mp4")
MAX_ANALYSIS_ATTEMPTS = 3
MAX_POLL_COUNT = 8
POLL_INTERVAL_SECONDS = 5


def ensure_credentials() -> None:
    if not AK or not SK:
        raise RuntimeError(
            "未配置 LIFE_EMERGENCE_AK / LIFE_EMERGENCE_SK 环境变量，无法调用舌面分析接口。"
        )


def canonicalize_json(value: Any):
    if value is None:
        return None
    if isinstance(value, dict):
        return {
            key: canonicalize_json(item)
            for key, item in sorted(value.items())
            if item is not None
        }
    if isinstance(value, list):
        return [canonicalize_json(item) for item in value]
    return value


def sha256_hex_of_json(body: Any) -> str:
    canonical = canonicalize_json(body)
    body_json = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body_json.encode("utf-8")).hexdigest()


def sign_request(method: str, headers: dict[str, str], request_body: Any) -> str:
    ensure_credentials()
    lower_headers = {key.lower(): value for key, value in headers.items()}
    access_key = lower_headers["x-access-key"]
    timestamp = lower_headers["x-timestamp"]
    nonce = lower_headers["x-nonce"]

    lines = [method.upper()]
    if request_body is not None:
        lines.append(sha256_hex_of_json(request_body))

    sign_headers = lower_headers.get("x-sign-headers")
    if sign_headers:
        header_names = [item.strip().lower() for item in sign_headers.split(":") if item.strip()]
        header_lines = [f"{name}:{lower_headers.get(name, '')}" for name in header_names]
        lines.append("\n".join(header_lines))

    string_to_sign = "\n".join(lines)
    sign_input = f"{access_key}{timestamp}{nonce}{string_to_sign}"
    return hmac.new(SK.encode("utf-8"), sign_input.encode("utf-8"), hashlib.sha256).hexdigest().upper()


def build_headers(method: str, body: Any = None) -> dict[str, str]:
    ensure_credentials()
    headers = {
        "X-Access-Key": AK,
        "X-Timestamp": str(int(time.time() * 1000)),
        "X-Nonce": str(uuid.uuid4()),
    }
    headers["X-Signature"] = sign_request(method, headers, body)
    return headers


def resolve_video_path() -> Path:
    if VIDEO_PATH.exists():
        return VIDEO_PATH

    candidates = list(Path(r"D:\huiliao").rglob("test_vedio.mp4"))
    if not candidates:
        raise FileNotFoundError(f"未找到测试视频: {VIDEO_PATH}")
    return candidates[0]


def start_health_analysis_with_payload(video_path: Path) -> dict[str, Any]:
    headers = build_headers("POST", None)
    with video_path.open("rb") as file_obj:
        files = {
            "file": (video_path.name, file_obj, "application/octet-stream"),
        }
        response = requests.post(
            BASE_URL + START_PATH,
            headers=headers,
            files=files,
            timeout=60,
        )

    print("start status:", response.status_code)
    print("start response:", response.text)
    response.raise_for_status()

    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"启动舌面分析失败: {payload}")
    return payload


def start_health_analysis(video_path: Path) -> str:
    payload = start_health_analysis_with_payload(video_path)
    analysis_id = (payload.get("data") or {}).get("analysisId")
    if not analysis_id:
        raise RuntimeError(f"返回中没有 analysisId: {payload}")
    return analysis_id


def query_health_analysis(analysis_id: str) -> dict[str, Any]:
    body = {"analysisId": analysis_id}
    headers = build_headers("POST", body)
    headers["Content-Type"] = "application/json"
    response = requests.post(
        BASE_URL + QUERY_PATH,
        headers=headers,
        json=body,
        timeout=30,
    )
    print("query status:", response.status_code)
    print("query response:", response.text)
    response.raise_for_status()
    return response.json()


def wait_for_health_analysis(
    video_path: Path,
    max_poll_count: int = MAX_POLL_COUNT,
    poll_interval_seconds: int = POLL_INTERVAL_SECONDS,
) -> dict[str, Any]:
    start_payload = start_health_analysis_with_payload(video_path)
    analysis_id = (start_payload.get("data") or {}).get("analysisId")
    if not analysis_id:
        raise RuntimeError(f"返回中没有 analysisId: {start_payload}")

    last_result: Optional[dict[str, Any]] = None
    for index in range(max_poll_count):
        if index > 0:
            time.sleep(poll_interval_seconds)

        result = query_health_analysis(analysis_id)
        last_result = result
        data = result.get("data")

        if result.get("success") is False:
            return {
                "analysisId": analysis_id,
                "tips": (start_payload.get("data") or {}).get("tips"),
                "startPayload": start_payload,
                "result": result,
            }

        if data and (data.get("faceAnalysisResponse") is not None or data.get("needRefresh") is False):
            return {
                "analysisId": analysis_id,
                "tips": (start_payload.get("data") or {}).get("tips"),
                "startPayload": start_payload,
                "result": result,
            }

    return {
        "analysisId": analysis_id,
        "tips": (start_payload.get("data") or {}).get("tips"),
        "startPayload": start_payload,
        "result": last_result,
        "timeout": True,
    }


def main():
    video_path = resolve_video_path()
    print("video path:", video_path)

    last_error = None
    for attempt in range(1, MAX_ANALYSIS_ATTEMPTS + 1):
        print(f"analysis attempt: {attempt}/{MAX_ANALYSIS_ATTEMPTS}")
        response = wait_for_health_analysis(video_path)
        result = response.get("result") or {}

        if response.get("timeout"):
            last_error = {"errorCode": "LOCAL_POLL_TIMEOUT", "errorMsg": "轮询结束，仍未拿到舌面分析结果"}
            continue

        if result.get("success") is False:
            last_error = result
            if result.get("errorCode") == "HEALTH_ANALYSIS_TIMEOUT":
                print("analysis timed out on server, retrying a new task...")
                continue
            raise RuntimeError(f"查询失败: {result}")

        print("analysisId:", response.get("analysisId"))
        if response.get("tips"):
            print("tips:", response.get("tips"))
        print("final result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    raise RuntimeError(f"多次尝试后仍未成功: {last_error}")


if __name__ == "__main__":
    main()