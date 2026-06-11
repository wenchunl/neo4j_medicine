from qa import MedicineQA

def main():
    qa = MedicineQA()
    print("医药知识图谱问答系统已启动，输入 exit 退出。")
    while True:
        question = input("请输入您的问题：")
        if question.lower() in ["exit", "退出", "quit"]:
            break
        answer = qa.answer(question)
        print("答案：", answer)


if __name__ == "__main__":
    main()