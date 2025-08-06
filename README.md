# AI4Exam

这是一个由人工智能驱动的应用程序，用于根据您上传的知识源文本生成练习题。



## 入门指南

这些说明将帮助您在本地计算机上获取并运行该项目的副本，以进行开发和测试。

### 环境要求

-   已安装 Python 3.8+
-   Node.js 和 npm (用于前端)
## 初次使用
### 安装

1.  **克隆仓库**

    ```sh
    git clone https://github.com/lihaozhang01/AI4exam.git
    cd ai4exam
    ```

2.  **后端设置 (Python)**

    -   进入 `backend` 目录：
        ```sh
        cd backend
        ```

    -   创建 Python 虚拟环境并运行：

        -   在 Windows 上：
            ```sh
            python -m venv venv
            .\venv\Scripts\activate
            ```

        -   在 macOS/Linux 上：
            ```sh
            python3 -m venv venv
            source venv/bin/activate
            ```

    -   安装所需的 Python 包：
        ```sh
        pip install -r requirements.txt
        ```

3.  **前端设置 (React)**

    -   进入 `ai4exam-frontend` 目录：
        ```sh
        cd ../ai4exam-frontend
        ```

    -   安装所需的 npm 包：
        ```sh
        npm install
        ```
## 创建脚本
- 为了方便使用，您可以创建一个脚本文件，用于启动后端和前端服务器。
- 在项目根目录下创建一个名为 `run.sh` 的文件（或 `run.bat`，根据您的操作系统），并添加以下内容：

  -   **对于 macOS/Linux (`run.sh`)**:
      ```sh
      #!/bin/bash

      # 激活后端虚拟环境并启动服务器
      echo "Starting backend server..."
      cd backend
      source venv/bin/activate
      uvicorn main:app --reload &
      cd ..

      # 启动前端开发服务器
      echo "Starting frontend development server..."
      cd ai4exam-frontend
      npm run dev
      ```

  -   **对于 Windows (`run.bat`)**:
      ```bat
      @echo off

      ECHO "Starting backend server..."
      start "Backend" cmd /k "cd backend && .\venv\Scripts\activate && uvicorn main:app --reload"

      ECHO "Starting frontend development server..."
      start "Frontend" cmd /k "cd ai4exam-frontend && npm run dev"
      ```
## 使用
创建脚本后，您可以直接运行脚本文件，而无需手动启动后端和前端服务器。
- 对于 macOS/Linux，运行 `./run.sh`。
- 对于 Windows，在项目文件夹中打开命令提示符或PowerShell中运行 `./run.bat`。
- 脚本将自动启动后端服务器和前端开发服务器。
- **在浏览器中打开 `http://localhost:5173` 即可开始使用应用程序。**
或者
- 您也可以手动启动后端和前端服务器。
1.  **运行后端服务器**

    -   在 `backend` 目录下运行：
        ```sh
        uvicorn main:app --reload
        ```
    -   后端 API 将在 `http://127.0.0.1:8000` 上可用。

2.  **运行前端开发服务器**

    -   在 `ai4exam-frontend` 目录下运行：
        ```sh
        npm run dev
        ```
    -   前端应用程序将在 `http://localhost:5173` 上可用。

3. **使用方式**
  - 打开应用程序后，您将看到一个简单的用户界面。
  - 初次使用时，请先点击右下角的齿轮图标，进入设置界面，配置您希望使用的模型及API密钥。
  - **配置完成后，点击“保存”按钮。**
  - 点击“上传文件”按钮，选择要上传的知识源文本文件（目前仅支持文本文件）。
  - 您可以在设置中设置自己的提示词，或在描述中输入您的需求，例如“减少对学科发展历史的考察，侧重理论基础和应用实例”。
  - **点击“生成练习题”按钮，应用程序将根据您的输入生成练习题。**
  - 生成完成后，您可以在应用程序中查看练习题，并进行练习。
  - 练习完成后，您可以点击“提交”按钮提交您的答案，应用程序将根据您的答案给出反馈。
  - 您也可以点击单题反馈，或者点击全题反馈，查看练习题的详细反馈（**同样建议您使用自己的点评模板**）。

![应用截图](docs/images/开始界面.png)
![应用截图](docs/images/设置界面.png)