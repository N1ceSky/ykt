import asyncio
import datetime
import random
import time

import toml
from bs4 import BeautifulSoup
from prettytable import SINGLE_BORDER, PrettyTable
from tqdm import tqdm

from database import YKTBase
from decode import decrypt, format_string
from ykt import YKT, CookiesManager

config = toml.load("config.toml")
# 记录已经做过的题目
isRecord = config.get("isRecord", True)
# 默认不跳过答题
isSkipQuiz = config.get("isSkipQuiz", False)


def html2Str(htmlStr):
    soup = BeautifulSoup(htmlStr, "html.parser")
    texts = [text.strip() for text in soup.stripped_strings]
    return "\n".join(texts)


def printCourseList(courseList):
    """打印课程列表"""
    table = PrettyTable()
    table.set_style(SINGLE_BORDER)
    table.field_names = ["#", "课程"]
    for index, course in enumerate(courseList):
        table.add_row(
            [
                index,
                course["course"]["name"],
            ]
        )
    print("\n" + table.get_string() + "\n")


def printDissList(dissList):
    """打印课程列表"""
    for index, diss in enumerate(dissList):
        print(f"\033[92m{index}\033[0m {diss}")


def printCourseSchedule(title, detail):
    """打印课程进度"""
    table = PrettyTable()
    table.title = title
    table.field_names = ["视频进度", "课程得分"]
    table.min_width = len(title)
    table.add_row(
        [f"{detail['videos_complete_progress']*100:.2f}%", detail["user_final_score"]]
    )
    table.set_style(SINGLE_BORDER)
    print("\n" + table.get_string())


def delay(left=10, right=20):
    """随机延迟
    动态更新的输出
    倒计时结束自动清空控制台输出
    """
    # 隐藏控制台光标
    print("\x1b[?25l", end="")
    sleepTime = random.randint(left, right)
    for i in range(sleepTime, 0, -1):
        print(
            f"等待{i:03}秒\r", end="", flush=True
        )  # 回到行首并打印新数字，end=''表示不换行，flush=True确保立即输出
        time.sleep(1)
    # 清空控制台输出
    print(" " * 10 + "\r", end="")
    # 显示控制台光标1
    print("\x1b[?25h", end="")
    return sleepTime


def inputDiss(discussList):
    """输入或者选择评论"""
    while True:
        prompt = input('输入序号选择已有评论(输入"#"自由输入)：')
        if prompt.strip() == "#":
            diss = input("请输入评论：")
            break
        else:
            try:
                index = int(prompt)
                if index >= 0 and index < len(discussList):
                    diss = discussList[index]
                    break
            except Exception:
                pass
    return diss


def copeVedio(leaf):
    """处理视频任务
    主要是两个请求
    发送心跳包和刷新任务进度
    """
    # int类型id
    ykt.leafStatus = ykt.getLeafInfo(leaf["id"])["data"]
    data = ykt.getVedioWatchProgess(leaf["id"])
    if str(leaf["id"]) in data:
        # 没刷完的
        data = data[str(leaf["id"])]
        ykt.cp = data["last_point"]
        ykt.tp = ykt.cp
        ykt.duration = data["video_length"]
    isFirst = True
    print("\n" + leaf["title"])
    # 隐藏控制台光标
    print("\x1b[?25l", end="")
    with tqdm(total=100, ncols=80) as pbar:
        while True:
            ykt.heartbeat(leaf["id"], isFirst)
            data = ykt.getVedioWatchProgess(leaf["id"])[str(leaf["id"])]
            ykt.cp = data["last_point"]
            ykt.duration = data["video_length"]
            isFirst = False
            pbar.update(round(data["rate"] * pbar.total) - pbar.n)
            if data["rate"] < 0.99 and ykt.cp == ykt.duration:
                # 有部分没刷到
                ykt.cp = 0
            if data["rate"] >= 0.99:
                pbar.update(pbar.total - pbar.n)
                break
            else:
                time.sleep(5)

    # 显示控制台光标1
    print("\x1b[?25h", end="")


def copeDiscuss(leaf):
    """处理讨论任务"""
    ykt.leafStatus = ykt.getLeafInfo(leaf["id"])["data"]
    topic = ykt.getDiscussion(
        leaf["id"], channel=ykt.leafStatus.get("third_platform_code", "")
    )["data"]
    topicId = topic["id"]
    context = html2Str(ykt.leafStatus["content_info"]["context"])
    query = format_string(context).replace("/n", "")
    diss = db.searchDiss(query)
    print("\n讨论", ykt.leafStatus["name"] + "\n" + context)
    if not diss:
        data = ykt.getDiscussionList(leaf["id"], topicId)["data"]
        discussList_ = (
            data["good_comment_list"]["results"] + data["new_comment_list"]["results"]
        )
        discussList = [diss["content"]["text"] for diss in discussList_[:5]]
        printDissList(discussList)
        diss = inputDiss(discussList)
        db.submitDiss(query, diss)
    # 提交评论
    data = ykt.comment(
        leafId=leaf["id"], topicId=topicId, toUserId=topic["user_id"], text=diss
    )
    print("提交", diss)


def record(question, options, answer, ptype):
    """记录正确答案"""
    if ptype == 6:
        # 判断题
        answer = ["A" if answer[0] == "true" else "B"]

    if ptype == 4:
        # 填空题 存储时不排序
        # 默认只有一个元素
        answer = [ans[0] for ans in answer.values()]
        db.submit(question, "|".join(answer))
    else:
        db.submit(
            "|".join([question, *sorted(options.values())]),
            "|".join(sorted([options[ans] for ans in answer])),
        )


def choice(ProblemType, options):
    """处理单选多选判断题"""
    while True:
        answer = input("请输入答案：").strip().upper()
        # 防呆
        if ProblemType in [1, 3, 6] and len(answer) == 1 and answer in options.keys():
            # 单选1 投票3 和判断6 只有一个选项
            answer = [answer]
            break
        elif ProblemType in [2, 3] and len(answer) >= 1:
            # 多选 投票3
            answer_ = [ans for ans in answer if ans in options.keys()]
            if len(answer) == len(answer_):
                answer = answer_
                break
    return answer


def copeQuiz(leaf):
    """处理答题任务"""
    ykt.leafStatus = ykt.getLeafInfo(leaf["id"])["data"]
    quizLeafInfo = ykt.getProblems()["data"]
    print("\n" + quizLeafInfo["name"])
    problems = quizLeafInfo["problems"]
    # 字体链接
    ttf_url = quizLeafInfo["font"]
    for index, problem in enumerate(problems):
        problemInfo = problem["content"]
        ProblemType = problemInfo["ProblemType"]
        question = decrypt(problemInfo["Body"], ttf_url)
        if ProblemType == 6:
            options = {
                "A": "正确" if problemInfo["Options"][0]["key"] == "true" else "错误",
                "B": "正确" if problemInfo["Options"][1]["key"] == "true" else "错误",
            }
        elif ProblemType == 4:
            # 填空题
            options = {}
        else:
            options = {
                o["key"]: decrypt(o["value"], ttf_url) for o in problemInfo["Options"]
            }
        if problem["user"]["my_count"] > 0:
            if isRecord:
                # 记录答案
                record(
                    question,
                    options,
                    problem["user"]["answers" if ProblemType == 4 else "answer"],
                    ProblemType,
                )
                print("收录 =>", question)
            # 跳过做过的题
            continue
        # 查询结果是 答案1|答案2 的形式 需要转换为选项
        answer = db.search(f"%{'|'.join([question, *sorted(options.values())])}%")
        if answer:
            if ProblemType == 4:
                answer = {i: ans for i, ans in enumerate(answer.split("|"))}
            else:
                options_ = {v: k for k, v in options.items()}
                answer = [options_[ans] for ans in answer.split("|")]
        else:
            # 打印题目
            print(f"\n{index+1}/{len(problems)}", problemInfo["TypeText"], question)
            for k, v in options.items():
                print(f"{k}:", v)
            # 手动填写
            if ProblemType == 4:
                answer = {}
                for blank in problemInfo["Blanks"]:
                    answer[str(blank["Num"])] = input(f"第{blank['Num']}空：").strip()
            else:
                answer = choice(ProblemType, options)

        if ProblemType == 6:
            # 判断题
            answer = ["true" if options[answer[0]] == "正确" else "false"]
        data = ykt.submitProblem(
            answer,
            problem["problem_id"],
            key="answers" if ProblemType == 4 else "answer",
        )["data"]
        # 记录正确答案
        record(
            question,
            options,
            data["answers" if ProblemType == 4 else "answer"],
            ProblemType,
        )
        print(
            "🎉 回答正确" if data["is_correct"] else "🔨 回答错误",
            f"得分：{data['my_score']} / {problem['score']}",
        )
        time.sleep(1)


def copeGraphic(leaf):
    ykt.leafStatus = ykt.getLeafInfo(leaf["id"])["data"]
    ykt.read(leafId=leaf["id"])
    print("\n图文", ykt.leafStatus["name"], "已读")
    time.sleep(1)


def copeLeaf(leaf):
    """处理leaf"""

    # 未完成的任务
    if leaf["leaf_type"] == 0:
        if leaf["schedule"] != 1:
            copeVedio(leaf)
    elif leaf["leaf_type"] == 3:
        if leaf["schedule"] != 1:
            copeGraphic(leaf)
    elif leaf["leaf_type"] == 4:
        # 无法获取发言列表无法记录之前的讨论
        if leaf["schedule"] != 1:
            copeDiscuss(leaf)
    elif not isSkipQuiz and leaf["leaf_type"] == 6:
        if isRecord or leaf["schedule"] != 1:
            # 未完成或者要记录题目
            copeQuiz(leaf)


def copeAct(activities):
    """处理全部活动"""
    for act in activities:
        ykt.current_act = act
        # 获取当前课程进度
        detail = ykt.getCourseDetail()["data"]
        leafInfos = detail["leaf_level_infos"]
        ykt.progess = {info["id"]: info for info in leafInfos}
        # 拉取章节列表
        courseData = ykt.getCourseContent()
        ykt.content = courseData["data"]["content_info"]
        # 打印任务进度
        printCourseSchedule(ykt.course_name, detail)
        # leafTypeDict = {0: "视频", 3: "图文", 4: "讨论", 6: "作业"}
        for charter in ykt.content:
            schedules = []
            for section in charter["section_list"]:
                for leaf in section["leaf_list"]:
                    leaf["schedule"] = ykt.progess.get(leaf["id"], {}).get(
                        "schedule", 0
                    )
                    if leaf["leaf_type"] in [0, 6]:
                        schedules.append(leaf["schedule"])
                    copeLeaf(leaf)
            for leaf in charter["leaf_list"]:
                leaf["schedule"] = ykt.progess.get(leaf["id"], {}).get("schedule", 0)
                if leaf["leaf_type"] in [0, 6]:
                    schedules.append(leaf["schedule"])
                copeLeaf(leaf)
            if len(schedules) and (sum(schedules) / len(schedules)) < 1:
                delay(8, 12)


def copeCourse():
    """拿到课程列表并选择课程"""
    courseList = ykt.getCourseList()["data"]["list"]
    # 过滤 只显示当年的课程
    if config.get("isFilter", True):
        year = datetime.datetime.now().year
        courseList = [
            course for course in courseList if year == int(course["term"] / 100)
        ]
    printCourseList(courseList)
    # 选课程 序号从0开始 对应printCourseList中的序号
    while True:
        index = int(input("请输入课程序号："))
        if index >= 0 and index < len(courseList):
            break
    ykt.current_course = courseList[index]
    # 拉取课程信息
    activities = ykt.getCourseInfo()["data"]["activities"]
    # 有效活动类型 过滤只留下列表内的活动
    valid_type = [15]
    activities = [act for act in activities if act["type"] in valid_type]
    copeAct(activities)


if __name__ == "__main__":
    ykt = YKT()
    manager = CookiesManager()
    manager.choice()

    if time.time() < manager.expires_time and manager.cookies:
        # 传递登录状态
        ykt.session.cookies = manager.cookies
        infoData = ykt.checkInfo()
        if infoData["code"] == 0:
            print(f"你好，{infoData['data']['name']}")
            isLogin = True
            # 账号名和实际名不同也重新登录
            if infoData["data"]["name"] != manager.name:
                isLogin = False
        else:
            isLogin = False
    else:
        isLogin = False

    if not isLogin:
        print("登录状态失效，重新登录")
        # 运行异步函数
        asyncio.run(ykt.qrLogin())
        infoData = ykt.checkInfo()
        if infoData["code"] == 0:
            print(f"你好，{infoData['data']['name']}")
            # 保存登录cookie为pkl文件
            manager.save(infoData["data"]["name"], ykt.session.cookies)
    db = YKTBase()
    copeCourse()
