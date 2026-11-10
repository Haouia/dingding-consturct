# tests/test_services.py —— python-svc 三个 FastAPI 服务的单元测试
#
# 覆盖：
#   /analyze         正常返回 / ```json 围栏解析 / 畸形 JSON 默认值 / LLM 异常 -> 503
#   /feed            2~4 条且字段齐全
#   /generate_report 正常生成 / 空记录 / LLM 异常兜底
#   导入安全          无 ALI_API_KEY 时 app.py、report_gen.py 仍可 import
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app as analysis_app
import news_feed_service as feed_app
import report_gen as report_app

SVC_DIR = Path(__file__).resolve().parents[1]

ANALYZE_BODY = {
    "title": "产品被大量投诉",
    "content": "这款产品最近差评如潮，客服电话被打爆，用户要求退款。",
    "source": "weibo",
}


# ========== 假的大模型客户端 ==========
class FakeCompletions:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=self.content)),
            ]
        )


class FakeClient:
    def __init__(self, content=None, error=None):
        self.completions = FakeCompletions(content=content, error=error)
        self.chat = SimpleNamespace(completions=self.completions)


def make_fake_client(content=None, error=None) -> FakeClient:
    return FakeClient(content=content, error=error)


def load_fresh(module_name: str, filename: str):
    """按文件路径重新加载一个模块副本，用于验证 import 期行为（不污染已导入模块）。"""
    spec = importlib.util.spec_from_file_location(module_name, SVC_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ========== fixtures ==========
@pytest.fixture()
def analysis_client():
    with TestClient(analysis_app.app) as client:
        yield client


@pytest.fixture()
def feed_client():
    with TestClient(feed_app.app) as client:
        yield client


@pytest.fixture()
def report_client():
    with TestClient(report_app.app) as client:
        yield client


# ========== /analyze ==========
def test_analyze_returns_structured_result(monkeypatch, analysis_client):
    fake = make_fake_client(
        content=json.dumps(
            {"sentiment": "负面", "level": "高", "reason": "差评如潮，大量退款诉求"},
            ensure_ascii=False,
        )
    )
    monkeypatch.setattr(analysis_app, "client", fake)

    resp = analysis_client.post("/analyze", json=ANALYZE_BODY)

    assert resp.status_code == 200
    body = resp.json()
    assert body["sentiment"] == "负面"
    assert body["level"] == "高"
    assert body["reason"] == "差评如潮，大量退款诉求"
    assert body["source"] == "weibo"  # N8N 工作流依赖 source 字段
    assert body["title"] == ANALYZE_BODY["title"]
    assert body["content"] == ANALYZE_BODY["content"]


def test_analyze_parses_fenced_json(monkeypatch, analysis_client):
    payload = {"sentiment": "正面", "level": "低", "reason": "用户口碑回暖"}
    fenced = "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"
    monkeypatch.setattr(analysis_app, "client", make_fake_client(content=fenced))

    body = analysis_client.post("/analyze", json=ANALYZE_BODY).json()

    assert body["sentiment"] == "正面"
    assert body["level"] == "低"
    assert body["reason"] == "用户口碑回暖"


def test_analyze_malformed_json_falls_back_to_defaults(monkeypatch, analysis_client):
    monkeypatch.setattr(
        analysis_app, "client", make_fake_client(content="抱歉，这不是合法的 JSON")
    )

    resp = analysis_client.post("/analyze", json=ANALYZE_BODY)

    assert resp.status_code == 200
    body = resp.json()
    assert body["sentiment"] == "中性"
    assert body["level"] == "低"
    assert body["reason"] == ""
    assert body["source"] == "weibo"


def test_analyze_llm_error_returns_503(monkeypatch, analysis_client):
    monkeypatch.setattr(
        analysis_app, "client", make_fake_client(error=RuntimeError("upstream boom"))
    )

    resp = analysis_client.post("/analyze", json=ANALYZE_BODY)

    assert resp.status_code == 503
    assert "大模型调用失败" in resp.json()["detail"]
    assert "upstream boom" in resp.json()["detail"]


# ========== /feed ==========
def test_feed_returns_two_to_four_complete_items(feed_client):
    resp = feed_client.get("/feed")

    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert 2 <= len(items) <= 4
    for item in items:
        assert set(item) >= {"title", "content", "source"}
        for key in ("title", "content", "source"):
            assert isinstance(item[key], str) and item[key].strip()


# ========== /generate_report ==========
def test_generate_report_returns_llm_report(monkeypatch, report_client):
    fake = make_fake_client(content="# 今日舆情简报\n舆情整体平稳。")
    monkeypatch.setattr(report_app, "client", fake)

    resp = report_client.post(
        "/generate_report",
        json={"records": [{"title": "服务器宕机", "sentiment": "负面", "level": "高"}]},
    )

    assert resp.status_code == 200
    assert resp.json()["report"] == "# 今日舆情简报\n舆情整体平稳。"
    # 记录确实被拼进 prompt 发给了模型
    user_prompt = fake.completions.last_kwargs["messages"][1]["content"]
    assert "服务器宕机" in user_prompt


def test_generate_report_empty_records_skips_llm(monkeypatch, report_client):
    fake = make_fake_client(content="不应被调用")
    monkeypatch.setattr(report_app, "client", fake)

    resp = report_client.post("/generate_report", json={"records": []})

    assert resp.status_code == 200
    assert resp.json() == {"report": "今日暂无舆情记录。"}
    assert fake.completions.last_kwargs is None


def test_generate_report_llm_error_is_returned_in_body(monkeypatch, report_client):
    monkeypatch.setattr(
        report_app, "client", make_fake_client(error=RuntimeError("upstream down"))
    )

    resp = report_client.post(
        "/generate_report", json={"records": [{"title": "数据泄露"}]}
    )

    assert resp.status_code == 200
    report = resp.json()["report"]
    assert "报告生成失败" in report
    assert "upstream down" in report


# ========== import 期安全（无 ALI_API_KEY） ==========
def test_modules_import_without_api_key(monkeypatch):
    monkeypatch.delenv("ALI_API_KEY", raising=False)

    for module_name, filename in (
        ("fresh_app", "app.py"),
        ("fresh_report_gen", "report_gen.py"),
    ):
        module = load_fresh(module_name, filename)
        assert module.API_KEY == ""
        assert module.client is not None
        assert module.client.api_key == "missing"
