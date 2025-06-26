import json
import time
from pathlib import Path

import qrcode
import requests
import websockets

QRCODE_PATH = Path("./qrcode.png")


def printQR(url):
    # 打印并保存登录二维码
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.print_ascii()
    img = qr.make_image()
    img.save(QRCODE_PATH)


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"


class YKT:
    # 选择的课程
    current_course = {}
    # 课程下有效的活动列表
    activities = []
    # 当前处理的活动
    current_act = {}
    # 全部章节
    content = []
    progess = {}
    # 当前章节的状态信息
    leafStatus = {}
    # 读取视频进度时初始化
    cp = 0
    # 本次播放开始的进度 仅在第一次读取视频进度时初始化
    tp = 0
    # 获取视频进度时初始化
    duration = 0

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})

    @property
    def course_name(self):
        # 返回字符串类型
        return self.current_course["course"]["name"]

    @property
    def courseware_id(self):
        # 返回字符串类型
        return self.current_act.get("courseware_id", "")

    @property
    def classroom_id(self):
        """例如 21575259"""
        return str(self.current_course.get("classroom_id", ""))

    @property
    def university_id(self):
        return str(self.current_course.get("course", {}).get("university_id", ""))

    @property
    def cid(self):
        """例如 4708851"""
        return str(self.current_course.get("course", {}).get("id", ""))

    @property
    def user_id(self):
        """例如 79480201"""
        return str(self.leafStatus.get("user_id", ""))

    @property
    def ccid(self):
        """答题任务时media为空对象"""
        return self.leafStatus.get("content_info", {}).get("media", {}).get("ccid", "")

    @property
    def leaf_type_id(self):
        """阅读任务时不存在 答题任务存在"""
        return self.leafStatus.get("content_info", {}).get("leaf_type_id", 0)

    @property
    def id(self):
        """章节id"""
        if self.leafStatus:
            return self.leafStatus["id"]
        else:
            return ""

    @property
    def timestamp(self):
        """时间戳"""
        return int(time.time() * 1000)

    @property
    def sku_id(self):
        """sku_id 例如 10628970"""
        return self.current_act.get("content", {}).get("sku_id", "")

    @property
    def csrf(self):
        return self.session.cookies["csrftoken"]

    def login(self, auth, UserID):
        # 将auth和UserID发送给服务器，拿到雨课堂的信息
        url = "https://www.yuketang.cn/pc/web_login"
        data = '{"UserID":' + str(UserID) + ',"Auth":"' + auth + '"}'

        # 无响应数据 cookie做登录状态保持 携带有过期时间
        self.session.post(url, data)

        # 登陆成功 删除二维码
        QRCODE_PATH.unlink()

    def getCourseList(self):
        url = "https://www.yuketang.cn/v2/api/web/courses/list?identity=2"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "uv-id": "0",
            "xt-agent": "web",
            "xtbz": "ykt",
        }
        response = self.session.get(url=url, headers=headers)

        return response.json()

    async def qrLogin(self):
        url = "wss://www.yuketang.cn/wsapp"  # WebSocket 服务器的 URI
        headers = {
            "User-Agent": UA,
            "Origin": "https://www.yuketang.cn",
        }
        data = {
            "op": "requestlogin",
            "role": "web",
            "version": 1.4,
            "type": "qrcode",
            "from": "web",
        }

        async with websockets.connect(url, additional_headers=headers) as websocket:
            # 将字典转换为JSON字符串并发送
            json_data = json.dumps(data)
            await websocket.send(json_data)
            # 保持连接并监听服务器的消息
            while True:
                response = await websocket.recv()
                if "qrcode" in response:
                    # 二维码信息 手动解包
                    response_json = json.loads(response)
                    printQR(url=response_json["qrcode"])

                if "subscribe_status" in response:
                    # 登录信息
                    json_data = json.loads(response)
                    self.login(auth=json_data["Auth"], UserID=json_data["UserID"])
                    break

    def getCourseInfo(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-client": "web",
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        params = {
            "actype": "-1",
            "page": "0",
            "offset": "20",
            "sort": "-1",
        }

        response = self.session.get(
            f"https://www.yuketang.cn/v2/api/web/logs/learn/{self.classroom_id}",
            params=params,
            headers=headers,
        )
        return response.json()

    def getCourseContent(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/studentLog/{self.classroom_id}",
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-client": "web",
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        response = requests.get(
            f"https://www.yuketang.cn/c27/online_courseware/xty/kls/pub_news/{self.courseware_id}/",
            headers=headers,
        )
        return response.json()

    def getProgess(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.yuketang.cn",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/studentLog/{self.classroom_id}",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-csrftoken": self.csrf,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        json_data = {
            "cid": "21575259",
            "new_id": [
                self.courseware_id,
            ],
        }

        response = self.session.post(
            "https://www.yuketang.cn/mooc-api/v1/lms/learn/course/pub_new_pro",
            headers=headers,
            json=json_data,
        )
        return response.json()["data"][self.courseware_id]

    def getLeafInfo(self, leafId):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/xcloud/video-student/{self.classroom_id}/{leafId}",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-client": "web",
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        response = self.session.get(
            f"https://www.yuketang.cn/mooc-api/v1/lms/learn/leaf_info/{self.classroom_id}/{leafId}/",
            headers=headers,
        )
        return response.json()

    def getVedioWatchProgess(self, leafId):
        # "referer": "https://www.yuketang.cn/v2/web/xcloud/video-student/21575259/50717636",
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        params = {
            "cid": self.cid,
            "user_id": self.user_id,
            "classroom_id": self.classroom_id,
            "video_type": "video",
            "vtype": "rate",
            "video_id": leafId,
            "snapshot": "1",
        }

        response = self.session.get(
            "https://www.yuketang.cn/video-log/get_video_watch_progress/",
            params=params,
            headers=headers,
        )
        return response.json()

    def heartbeat(self, leafId: int, isFirst=False):
        """心跳包 模拟观看"""

        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/xcloud/video-student/{self.classroom_id}/{leafId}",
            "classroom-id": self.classroom_id,
            "x-csrftoken": self.csrf,
            "x-requested-with": "XMLHttpRequest",
            "xtbz": "ykt",
        }
        sq = 1
        heart_data = []
        data_temp = {
            "i": 5,
            "p": "web",
            "n": "ali-cdn.xuetangx.com",
            "lob": "ykt",
            "fp": 0,
            "tp": self.tp,
            "sp": 1,
            "u": int(self.user_id),
            "uip": "",
            "c": int(self.cid),
            "v": leafId,
            "skuid": self.sku_id,
            "classroomid": self.classroom_id,
            "cc": self.ccid,
            "d": self.duration,
            "pg": f"{leafId}_qjls",
            "t": "video",
            "cards_id": 0,
            "slide": 0,
            "v_url": "",
        }
        if isFirst:
            dataList = ["loadstart", "loadeddata", "play", "playing"]
        else:
            dataList = ["heartbeat"] * 5
        sendTimeStamp = self.timestamp - 5000 * len(dataList)
        for data_et in dataList:
            data_temp["et"] = data_et
            data_temp["sq"] = sq
            if data_et == "loadstart":
                data_temp["cp"] = 0
                data_temp["d"] = 0
            elif data_et == "loadeddata":
                data_temp["cp"] = 0
            else:
                data_temp["cp"] = self.cp
            data_temp["ts"] = str(sendTimeStamp)
            sendTimeStamp += 5000
            if self.cp >= self.duration:
                # 播放结束
                data_temp["cp"] = self.duration
                heart_data.append(data_temp)
                break
            else:
                heart_data.append(data_temp)
            if data_et == "playing":
                sq += 5
            else:
                sq += 1
            if data_et in ["heartbeat"]:
                self.cp += 5

        json_data = {
            "heart_data": heart_data,
        }

        response = self.session.post(
            "https://www.yuketang.cn/video-log/heartbeat/",
            headers=headers,
            json=json_data,
        )
        return response

    def checkInfo(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        response = self.session.get(
            "https://www.yuketang.cn/api/v3/user/basic-info",
            headers=headers,
        )
        return response.json()

    def getCourseDetail(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/studentLog/{self.classroom_id}",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-csrftoken": self.csrf,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        response = self.session.get(
            f"https://www.yuketang.cn/c27/online_courseware/schedule/score_detail/single/{self.sku_id}/0/",
            headers=headers,
        )
        return response.json()

    def getProblems(self):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        response = self.session.get(
            f"https://www.yuketang.cn/mooc-api/v1/lms/exercise/get_exercise_list/{self.leaf_type_id}/",
            headers=headers,
        )
        return response.json()

    def submitProblem(self, answer, problemId, key="answer"):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.yuketang.cn",
            "referer": f"https://www.yuketang.cn/v2/web/cloud/student/exercise/{self.classroom_id}/{self.id}/{self.sku_id}",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-csrftoken": self.csrf,
            "xt-agent": "web",
            "xtbz": "ykt",
        }
        # 填空题key为answers
        json_data = {
            "classroom_id": int(self.classroom_id),
            "problem_id": problemId,
            key: answer,
        }

        response = self.session.post(
            "https://www.yuketang.cn/mooc-api/v1/lms/exercise/problem_apply/",
            headers=headers,
            json=json_data,
        )
        return response.json()

    def read(self, leafId):
        """
        阅读图文
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        params = {
            "cid": self.classroom_id,
            "sid": self.sku_id,
        }

        response = self.session.get(
            f"https://www.yuketang.cn/mooc-api/v1/lms/learn/user_article_finish/{leafId}/",
            params=params,
            headers=headers,
        )
        return response.json()

    def getDiscussionList(self, leafId, topicId):
        """获取讨论列表"""

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "referer": f"https://www.yuketang.cn/v2/web/lms/21575253/forum/{leafId}",
            "priority": "u=1, i",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        params = {
            "offset": "0",
            "limit": "10",
            "web": "web",
        }

        response = self.session.get(
            f"https://www.yuketang.cn/v/discussion/v2/comment/list/{topicId}/",
            params=params,
            headers=headers,
        )
        return response.json()

    def getDiscussion(self, leafId, channel):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/lms/{self.classroom_id}/forum/{self.id}",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-csrftoken": self.csrf,
            "xt-agent": "web",
            "xtbz": "ykt",
        }

        params = {
            "classroom_id": self.classroom_id,
            "sku_id": str(self.sku_id),
            "leaf_id": str(leafId),
            "topic_type": "4",
        }
        if channel:
            params["channel"] = channel

        response = self.session.get(
            "https://www.yuketang.cn/v/discussion/v2/unit/discussion/",
            params=params,
            headers=headers,
        )
        return response.json()

    def comment(self, leafId, topicId, toUserId, text):
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.yuketang.cn",
            "priority": "u=1, i",
            "referer": f"https://www.yuketang.cn/v2/web/lms/{self.classroom_id}/forum/{self.id}",
            "classroom-id": self.classroom_id,
            "university-id": self.university_id,
            "uv-id": self.university_id,
            "x-csrftoken": self.csrf,
            "xt-agent": "web",
            "xtbz": "ykt",
        }
        # to_user 50541248   topic_id 17240941
        json_data = {
            "to_user": toUserId,
            "topic_id": topicId,
            "content": {
                "text": text,
                "upload_images": [],
                "accessory_list": [],
            },
        }

        response = self.session.post(
            "https://www.yuketang.cn/v/discussion/v2/comment/",
            headers=headers,
            json=json_data,
        )
        return response.json()
