import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, TestPaper, DBQuestion, TestPaperResult # 确保从您的模型文件中导入

# --- 数据库设置 ---
DATABASE_URL = "sqlite:///F:\\ai4exam\\backend\\test.db"  # 使用绝对路径指向正确的 test.db

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# --- 创建数据库表 ---
# 这将检查所有继承自 Base 的模型，并在数据库中创建相应的表（如果它们还不存在）
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def print_test_paper_details_by_id(test_paper_id=None):
    """连接数据库，获取并打印第一份试卷的详细信息。"""
    db = SessionLocal()
    # --- 调试代码：检查数据库文件路径 ---
    db_path = DATABASE_URL.split('///')[-1]
    import os
    print(f"数据库文件绝对路径: {os.path.abspath(db_path)}")
    print(f"数据库文件是否存在: {os.path.exists(db_path)}")

    try:
        if test_paper_id:
            test_paper = db.query(TestPaper).filter(TestPaper.id == test_paper_id).first()
        else:
            # 获取第一份试卷，并预加载相关的问题
            test_paper = db.query(TestPaper).order_by(TestPaper.id.desc()).first()  

        if not test_paper:
            print("数据库中没有找到任何试卷。")
            return

        print(f"--- 试卷 ID: {test_paper.id} ---")
        print(f"试卷名称: {test_paper.name}")
        # print(f"来源内容: {test_paper.source_content}")
        print(f"创建时间: {test_paper.created_at}")
        print("\n--- 试卷包含的问题 ---")

        # 直接从关联关系中获取问题
        questions = test_paper.questions
        if not questions:
            print("这份试卷没有包含任何问题。")
        else:
            for i, q in enumerate(questions):
                print(f"\n--- 问题 {i+1} (ID: {q.id}) ---")
                print(f"  类型: {q.question_type}")
                print(f"  题干: {q.stem}")
                
                # 对 options 和 correct_answer 进行格式化输出
                if q.options:
                    # options 是 JSON 字符串，需要解析
                    try:
                        options_data = q.options
                        if isinstance(options_data, str):
                            options_data = json.loads(options_data)
                        print(f"  选项: {json.dumps(options_data, ensure_ascii=False, indent=4)}")
                    except json.JSONDecodeError:
                        print(f"  选项: {q.options} (非JSON格式)")
                
                if q.correct_answer:
                    # correct_answer 也是 JSON 字符串，需要解析
                    try:
                        answer_data = q.correct_answer
                        if isinstance(answer_data, str):
                            answer_data = json.loads(answer_data)
                        print(f"  正确答案: {json.dumps(answer_data, ensure_ascii=False, indent=4)}")
                    except json.JSONDecodeError:
                        print(f"  正确答案: {q.correct_answer} (非JSON格式)")

        # 查询并打印与该试卷相关的最新一份用户答案
        latest_result = db.query(TestPaperResult).filter(TestPaperResult.test_paper_id == test_paper.id).order_by(TestPaperResult.created_at.desc()).first()

        if not latest_result:
            print("\n--- 没有找到该试卷的用户提交记录 ---")
        else:
            print("\n--- 最新一份用户提交的答案 ---")
            print(f"提交时间: {latest_result.created_at}")
            
            user_answers = latest_result.user_answers
            if isinstance(user_answers, str):
                user_answers = json.loads(user_answers)
            
            print("用户答案详情:")
            print(json.dumps(user_answers, ensure_ascii=False, indent=4))

    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            paper_id = int(sys.argv[1])
            print_test_paper_details_by_id(paper_id)
        except ValueError:
            print("请输入一个有效的试卷ID（整数）。")
    else:
        print_test_paper_details_by_id()