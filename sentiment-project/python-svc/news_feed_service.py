# news_feed_service.py —— 本地模拟【舆情源】接口
import random
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="模拟舆情源")

NEWS_POOL = [
    # 全是高危负面，疯狂触发报警
    {"title": "产品被大量投诉", "content": "这款产品最近差评如潮，客服电话被打爆，用户要求退款。", "source": "weibo"},
    {"title": "服务器故障导致宕机", "content": "今天下午系统大面积宕机，用户无法登录，损失严重。", "source": "twitter"},
    {"title": "数据泄露传闻", "content": "有网友爆料用户数据疑似泄露，引发广泛担忧。", "source": "forum"},
    {"title": "严重客诉：系统扣款异常", "content": "多名用户反映被重复扣款，客服无人接听，准备集体投诉。", "source": "weibo"},
    {"title": "竞品恶意抹黑事件", "content": "网上出现大量有组织的水军发帖抹黑我司产品质量。", "source": "forum"},
]

@app.get("/feed")
def feed():
    """返回舆情列表（顶层是 JSON 数组）。每次随机抽 2~4 条"""
    k = random.randint(2, 4)
    return random.sample(NEWS_POOL, k=min(k, len(NEWS_POOL)))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) # 8002：舆情源