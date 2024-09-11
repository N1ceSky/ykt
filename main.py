import asyncio
import datetime
import os
import pickle
import random
import time

import toml
from prettytable import PrettyTable
from tqdm import tqdm

from ykt import YKT

config = toml.load("config.toml")


def printCourseList(courseList):
    """打印课程列表"""
    table = PrettyTable()
    table.field_names = ["课程", "考试"]
    for index, course in enumerate(courseList):
        table.add_row(
            [
                index,
                course["course"]["name"],
            ]
        )
    print("\n" + table.get_string() + "\n")


def delay(left=10, right=20):
    """随机延迟
    动态更新的输出
    倒计时结束自动清空控制台输出
    """
    sleepTime = random.randint(left, right)
    for i in range(sleepTime, 0, -1):
        print(
            f"等待{i:03}秒\r", end="", flush=True
        )  # 回到行首并打印新数字，end=''表示不换行，flush=True确保立即输出
        time.sleep(1)
    # 清空控制台输出
    print(" " * 10 + "\r", end="")
    return sleepTime


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


def copeQuiz(leaf):
    """处理答题任务"""


def copeAct(activities):
    """处理全部活动"""
    for act in activities:
        ykt.current_act = act
        # 打印任务详情
        print(
            f"包含{act['content']['c_n']}章，{act['content']['s_n']}小节，共计{act['content']['l_n']}个学习单元"
        )
        # 获取当前活动进度
        ykt.progess = ykt.getProgess()
        # 拉取章节列表
        courseData = ykt.getCourseContent()
        ykt.content = courseData["data"]["content_info"]
        # leafTypeDict = {0: "视频", 4: "讨论", 6: "作业"}
        for charter in ykt.content:
            for leaf in charter["leaf_list"]:
                if (id := str(leaf["id"])) in ykt.progess:
                    progess_ = ykt.progess[id]
                    if isinstance(progess_, dict):
                        # 题目类
                        leaf["progess"] = progess_["done"] / progess_["total"]
                    else:
                        leaf["progess"] = progess_
                else:
                    leaf["progess"] = 0
                if leaf["progess"] != 1:
                    # 未完成的任务
                    if leaf["leaf_type"] == 0:
                        copeVedio(leaf)
                    elif leaf["leaf_type"] == 4:
                        continue
                        # copeDiscuss(leaf)
                    elif leaf["leaf_type"] == 6:
                        continue
                        # copeQuiz(leaf)


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
    print(f"开始学习=>{ykt.current_course['course']['name']}")
    # 拉取课程信息
    activities = ykt.getCourseInfo()["data"]["activities"]
    # 有效活动类型 过滤只留下列表内的活动
    valid_type = [15]
    activities = [act for act in activities if act["type"] in valid_type]
    copeAct(activities)


if __name__ == "__main__":
    ykt = YKT()
    if os.path.exists("cookies.pkl"):
        with open("cookies.pkl", "rb") as f:
            cookies = pickle.load(f)
        # 失效时间
        expires_time = min([coo.expires for coo in cookies if coo.expires])
    else:
        expires_time = 0

    if time.time() < expires_time:
        # 传递登录状态
        ykt.session.cookies = cookies
        infoData = ykt.checkInfo()
        if infoData["code"] == 0:
            print(f"你好，{infoData['data']['name']}")
            isLogin = True
        else:
            isLogin = False
    else:
        isLogin = False

    if not isLogin:
        print("登录状态失效，重新登录")
        # 运行异步函数
        asyncio.run(ykt.qrLogin())
        # 保存登录cookie为pkl文件
        with open("cookies.pkl", "wb") as f:
            pickle.dump(ykt.session.cookies, f)
    copeCourse()
