# tests/conftest.py —— 让测试可以直接 import python-svc 下的平铺模块
import os
import sys
from pathlib import Path

SVC_DIR = Path(__file__).resolve().parents[1]
if str(SVC_DIR) not in sys.path:
    sys.path.insert(0, str(SVC_DIR))

# 在测试模块 import 之前兜底一个假 key：
# 即使有人把 app.py / report_gen.py 的 import 期加固改坏了，测试也能先加载起来并给出明确断言。
os.environ.setdefault("ALI_API_KEY", "test-key")
