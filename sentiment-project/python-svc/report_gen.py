# report_service.py —— 每日舆情报告生成 API 接口
import os
from datetime import datetime
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# 1. 初始化阿里云百炼客户端
# 未配置 ALI_API_KEY 时不阻断 import：服务照常启动，仅在真正生成报告时失败（接口内兜底）
API_KEY = os.getenv("ALI_API_KEY", "")
client = OpenAI(
    api_key=API_KEY or "missing",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    timeout=30,
)
MODEL = "qwen-max"

app = FastAPI(title="舆情报告生成服务")

# 定义接收 N8N 传来的数据格式
class ReportRequest(BaseModel):
    records: list[dict]

@app.post("/generate_report")
def generate_daily_report(req: ReportRequest):
    records = req.records
    if not records:
        return {"report": "今日暂无舆情记录。"}

    records_text = "\n".join(
        f"- [{r.get('sentiment', '未知')}/{r.get('level', '未知')}级] {r.get('title', '无标题')}" for r in records
    )

    today = datetime.now().strftime("%Y-%m-%d")

    system_prompt = (
        "你是一个资深的品牌舆情分析师。你需要根据提供的舆情记录，"
        "生成一份专业的每日舆情简报。"
    )

    user_prompt = f"""日期：{today}
以下是今日的舆情记录：
{records_text}

请严格按照以下三个模块生成报告：
1. **舆情总览**：概括今日整体的舆论走向（一句话总结）。
2. **重点舆情**：详细分析其中的高危及负面事件，说明潜在风险。
3. **应对建议**：针对负面/高危事件，给出具体的公关或客服处理建议。

请使用 Markdown 格式输出，内容精炼。"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        # 返回给 N8N，注意这里用字典包起来，N8N 才能解析成 JSON
        return {"report": response.choices[0].message.content}
    except Exception as e:
        return {"report": f"报告生成失败：{str(e)}"}

if __name__ == '__main__':
    # 端口用 8003，别和 8001（分析）、8002（抓取）冲突
    uvicorn.run(app, host='0.0.0.0', port=8003)