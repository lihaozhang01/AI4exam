import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# 从环境变量中获取 API 密钥
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("错误：请设置 GOOGLE_API_KEY 环境变量")
else:
    try:
        # 配置 API 密钥
        genai.configure(api_key=api_key)

        # 创建模型实例
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 生成内容
        response = model.generate_content("Explain how AI works in a few words")

        # 打印响应
        print(response.text)

    except Exception as e:
        print(f"调用 Gemini API 时发生错误: {e}")