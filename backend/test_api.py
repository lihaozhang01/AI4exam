import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 后端API的URL
BASE_URL = "http://127.0.0.1:8000"

def check_env():
    """检查环境变量是否配置正确"""
    # 加载当前目录的 .env 文件
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("错误：未找到 GOOGLE_API_KEY。")
        print("请在 'backend' 目录下创建一个名为 '.env' 的文件，并添加以下内容：")
        print("GOOGLE_API_KEY='Your-API-Key'")
        return False
    return True

def test_generate_test_api():
    """
    测试 /generate-test 接口
    """
    print("--- Testing /generate-test API ---")

    if not check_env():
        return

    # 1. 准备请求数据
    url = f"{BASE_URL}/generate-test"

    # 知识源文本
    source_text = "微观经济学是研究个体经济单位（如消费者、厂商）的经济行为，以及这些行为如何相互作用形成市场价格和资源配置的学科。核心概念包括供求理论、弹性、消费者行为理论、生产者理论、市场结构（完全竞争、垄断、寡头、垄断竞争）和市场失灵等。"

    # 试卷配置
    config = {
        "title": "微观经济学基础知识测验",
        "description": "本试卷旨在考察学生对微观经济学核心概念的理解。",
        "question_config": [
            {
                "type": "single_choice",
                "count": 5
            }
        ],
        "difficulty": "easy"
    }

    # 使用 application/x-www-form-urlencoded 格式发送请求
    data = {
        'source_text': source_text,
        'config_json': json.dumps(config),
    }

    # 2. 发送请求
    try:
        # 注意：这里改用 data 参数
        response = requests.post(url, data=data)
        response.raise_for_status()  # 如果状态码不是200, 则会引发HTTPError

        # 3. 解析并打印响应
        response_data = response.json()
        print("API call successful!")
        print("Test ID:", response_data.get("test_id"))
        print("Generated Questions:")
        print(json.dumps(response_data.get("questions", []), indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        if e.response is not None:
            print("Status Code:", e.response.status_code)
            try:
                # 尝试以JSON格式打印错误详情
                error_details = e.response.json()
                print("Error Details:", json.dumps(error_details, indent=2, ensure_ascii=False))
            except ValueError:
                # 如果响应不是JSON格式，直接打印响应文本
                print("Error Details:", e.response.text)


if __name__ == "__main__":
    test_generate_test_api()