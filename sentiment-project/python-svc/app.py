# Python 情感分析服务
"""
职责：接收舆情文本，调用大模型做情感分析
"""
import os
import json
import re
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# ========== 客户端初始化 ==========
# 未配置 ALI_API_KEY 时不阻断 import：服务照常启动，真正调用大模型时才失败（/analyze 返回 503）
API_KEY = os.getenv("ALI_API_KEY", "")

client = OpenAI(
    api_key=API_KEY or "missing",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    timeout=30,
)
MODEL = "qwen-max"

app = FastAPI(title="舆情情感分析服务")


# ========== 请求体数据契约 ==========
class News(BaseModel):
    title: str          # 舆情标题【必填】
    content: str        # 舆情正文【必填】
    source: str = "unknown"  # 来源【选填，默认 unknown】


# ========== JSON 解析兜底 ==========
def _extract_json(raw: str) -> dict:
    """把模型输出尽量解析成 dict"""
    if not raw:
        return {}
    text = raw.strip()
    # 去掉 ```json ... ``` 或 ``` ... ``` 围栏
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 从第一个 { 到最后一个 } 截取再试
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


# ========== 接口 ==========
@app.post("/analyze")
def analyze(news: News):
    """接收舆情 -> 调大模型分析 -> 返回结构化 JSON【情感、级别、原因】"""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是舆情分析专家，判断情感倾向并给出预警级别。预警级别代表危机程度：只有负面舆情才可能评为中/高，正面或中性新闻预警级别必须为低。只输出JSON。",
                },
                {
                    "role": "user",
                    "content": (
                        f"标题：{news.title}\n内容：{news.content}\n"
                        "请按以下规则分析：\n"
                        "1. sentiment: 正面/负面/中性\n"
                        "2. level: 高/中/低（负面且影响严重选高；负面但影响可控选中；正面、中性或轻微负面选低）\n"
                        "3. reason: 原因\n"
                        '只输出JSON，格式：{"sentiment":"...","level":"...","reason":"..."}'
                    ),
                },
            ],
            response_format={"type": "json_object"},  # 强制 JSON 输出
        )
    except Exception as e:
        # 大模型调用失败 -> 503，避免直接 500
        raise HTTPException(status_code=503, detail=f"大模型调用失败: {e}")

    # ✅ OpenAI SDK 返回的是对象，不是字典
    raw = resp.choices[0].message.content
    data = _extract_json(raw)

    return {
        "title": news.title,
        "content": news.content,
        "source": news.source,  # N8N 工作流依赖该字段，必须回传
        "sentiment": data.get("sentiment", "中性"),  # 安全默认值
        "level": data.get("level", "低"),
        "reason": data.get("reason", ""),
    }


# ========== 启动 ==========
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)