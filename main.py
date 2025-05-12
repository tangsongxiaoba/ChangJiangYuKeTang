# -*- coding: utf-8 -*-
# 长江雨课堂自动刷课脚本
# version 4
# developed by zk chen

import time
import requests
import re
import json
import logging
import colorama
from typing import Dict, List
import pprint


# 初始化日志配置
colorama.init(autoreset=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class YuKeTangAutomation:
    def __init__(self):
        # 初始化用户认证信息
        self.csrftoken = 's6G3UV9Vpt2eMcjE2QU7tldbiUqGaBrZ'
        self.sessionid = '6j08p0suzsts0hrbsx72xuyk03y75agr'
        self.uv_id = '3832'
        
        # 初始化请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/87.0.4280.67 Safari/537.36',
            'Content-Type': 'application/json',
            'Cookie': f'csrftoken={self.csrftoken}; sessionid={self.sessionid}; university_id={self.uv_id}; platform_id=3',
            'referer': 'https://changjiang.yuketang.cn/v2/web/index',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'university-id': self.uv_id,
            'uv-id': self.uv_id,
            'x-csrftoken': self.csrftoken,
            'xt-agent': 'web',
            'xtbz': 'cloud'
        }

        # 定义叶子节点类型
        self.leaf_type = {
            "video": 0,
            "homework": 6,
            "exam": 5,
            "recommend": 3,
            "discussion": 4
        }

    def watch_video(self, video_id: str, video_name: str, cid: str, user_id: str, classroomid: str, skuid: str) -> int:
        """观看单个视频

        Args:
            video_id: 视频ID
            video_name: 视频名称
            cid: 课程ID
            user_id: 用户ID
            classroomid: 教室ID
            skuid: SKU ID

        Returns:
            int: 1表示成功，0表示失败
        """
        # 获取视频观看进度的URL
        get_url = f"https://changjiang.yuketang.cn/video-log/get_video_watch_progress/?cid={cid}&user_id={user_id}&classroom_id={classroomid}&video_type=video&vtype=rate&video_id={video_id}&snapshot=1&term=latest&uv_id={self.uv_id}"
        progress = requests.get(url=get_url, headers=self.headers)

        data: Dict = json.loads(progress.text)["data"]
        video_length = 0
        video_frame = 0

        for v in data.values():
            video_length = v["video_length"]
            video_frame = v["last_point"]        
        print(f"{video_frame}")
        print(f"{video_length}")
        # 检查视频是否已完成
        if_completed = '0'
        try:
            if_completed = re.search(r'"completed":(.+?),', progress.text).group(1)
        except:
            pass

        if if_completed == '1':
            logging.info(f"《{video_name}》已经学习完毕，跳过")
            return 1
        else:
            logging.info(f"《{video_name}》尚未学习，现在开始自动学习")

        # 视频观看进度相关参数
    
        val = 0
        t = time.time()
        timestap = int(round(t * 1000))

        # 心跳请求URL
        url = "https://changjiang.yuketang.cn/video-log/heartbeat/"
        start = 0
        # 循环发送心跳请求直到视频完成
        while val != "1.0" and val != '1':
            this_type = 0 if start != 0 else 1
            heart_data, ts, vf = self._generate_heart_data(video_frame, timestap, user_id, cid, video_id, skuid, classroomid, video_length, 0)
            data = {"heart_data": heart_data}

            # pprint.pprint(data)
            r = requests.post(url=url, headers=self.headers, json=data)
            progress = requests.get(url=get_url, headers=self.headers)
            try:
                data = json.loads(progress.text)["data"]
                key = list(now_video.keys())[0]
                data = data[key]
                ts = timestap + (data["last_point"] - video_frame) * 1000
            except:
                data = {"ult": time.time() + 2, "last_point": -1}
                ts = time.time() * 1000 + 5000
            pprint.pprint(data)
            while (timestap <= ts):
                time.sleep(0.1)
                t = time.time()
                timestap = int(round(t * 1000))
            
            # 发送心跳请求
            
            # # 处理异常情况
            # try:
            #     error_msg = json.loads(r.text)["message"]
            #     if "anomaly" in error_msg:
            #         video_frame = 0
            # except:
            #     pass

            # try:
            #     # 处理网络阻塞情况
            #     delay_time = re.search(r'Expected available in(.+?)second.', r.text).group(1).strip()
            #     logging.warning(f"由于网络阻塞，要阻塞{delay_time}秒")
            #     time.sleep(float(delay_time) + 0.5)
            #     t = time.time()
            #     timestap = int(round(t * 1000))       
            #     video_frame = 0
            #     logging.info("恢复工作")
            # except:
            #     pass

            # 获取当前进度
            progress = requests.get(url=get_url, headers=self.headers)
            try:
                if_completed = re.search(r'"completed":(.+?),', progress.text).group(1)
                if if_completed == '1':
                    return 1
            except:
                pass
            pprint.pprint(progress.text)
            try:
                now_video: Dict = json.loads(progress.text)["data"]
                key = list(now_video.keys())[0]
                data = now_video[key]
                tmp_rate = re.search(r'"rate":(.+?)[,}]', progress.text)
                val = tmp_rate.group(1)
            except:
                data = {"last_point": 0}
                val = 0
            
            logging.info(f"学习进度：{float(val) * 100:.1f}% (last_point: {data['last_point']})")
            
            # 更新参数
            video_frame = data["last_point"]
            start += 1
            time.sleep(1)

        logging.info(f"视频《{video_name}》(ID: {video_id}) 学习完成")
        exit(-1)
        return 1

    def _generate_heart_data(self, video_frame: int, this_timestap: int, user_id: str, cid: str, 
                            video_id: str, skuid: str, classroomid: str, video_length: float, this_type=0):
        """生成心跳数据

        Args:
            video_frame: 视频帧
            timestap: 时间戳
            user_id: 用户ID
            cid: 课程ID
            video_id: 视频ID
            skuid: SKU ID
            classroomid: 教室ID

        Returns:
            List[Dict]: 心跳数据列表
        """
        import random
        heart_data = []
        start = 0
        timestap = this_timestap
        ran = random.choice([-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4])
        num = 6
        if this_type != 0:
            for name in ["loadstart", "loadeddata", "playing", "waiting", "playing"]:
                heart_data.append({
                    "c": cid,
                    "cards_id": 0,
                    "cc": video_id,
                    "classroomid": classroomid,
                    "cp": 0,
                    "d": video_length,
                    "et": name,
                    "fp": 0,
                    "i": 5,
                    "lob": "ykt",
                    "n": "ali-cdn.xuetangx.com",
                    "p": "web",
                    "pg": "32904324_18uvz",
                    "skuid": skuid,
                    "slide": 0,
                    "sp": 1,
                    "sq": start + 1,
                    "t": "video",
                    "tp": video_frame,
                    "ts": str(timestap + ran * 10),
                    "u": int(user_id),
                    "uip": "",
                    "v": int(video_id),
                    "v_url": "",
                })
                start += 1
                timestap += ran * 10
            num -= 2

        ret = 0
        ret2 = 0
        for i in range(1, num + 1):
            ran = random.choice([-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4])
            if i == num:
                ret = timestap + 5000 * i + ran * 1000
                ret2 = video_frame + i * 5 + ran
            heart_data.append({
                "c": cid,
                "cards_id": 0,
                "cc": video_id,
                "classroomid": classroomid,
                "cp": video_frame + i * 5 + ran,
                "d": video_length,
                "et": "heartbeat",
                "fp": 0,
                "i": 5,
                "lob": "ykt",
                "n": "ali-cdn.xuetangx.com",
                "p": "web",
                "pg": "32904324_18uvz",
                "skuid": skuid,
                "slide": 0,
                "sp": 1,
                "sq": start + 1,
                "t": "video",
                "tp": video_frame,
                "ts": str(timestap + 5000 * i + ran * 1000),
                "u": int(user_id),
                "uip": "",
                "v": int(video_id),
                "v_url": "",
            })
            start += 1
        return heart_data, ret, ret2

    def get_class_info(self, cid: str, video_id: str, name: str) -> None:
        """获取课程信息并观看视频

        Args:
            cid: 课程ID
            video_id: 视频ID
            name: 视频名称
        """
        get_url = f'https://changjiang.yuketang.cn/mooc-api/v1/lms/learn/leaf_info/{cid}/{video_id}/'
        response = requests.get(url=get_url, headers=self.headers).json()
        
        skuid = response['data']['sku_id']
        user_id = response['data']['user_id']
        course_id = response['data']['course_id']
        
        self.watch_video(video_id, name, course_id, str(user_id), cid, skuid)

    def process_course_content(self, content_info: List[Dict], cid: str) -> None:
        """处理课程内容

        Args:
            content_info: 课程内容信息
            cid: 课程ID
        """
        for section in content_info:
            if 'leaf_list' not in section:
                continue

            # 处理叶子节点列表
            if section['leaf_list']:
                for class_info in section['leaf_list']:
                    if class_info['leaf_type'] != 0:
                        logging.debug(f'《{class_info["title"]}》非视频，跳过')
                        continue
                    self.get_class_info(cid, class_info['id'], class_info['title'])

            # 处理小节列表
            if section['section_list']:
                for subsection in section['section_list']:
                    for class_info in subsection['leaf_list']:
                        if class_info['leaf_type'] != 0:
                            logging.debug(f'《{class_info["title"]}》非视频，跳过')
                            continue
                        self.get_class_info(cid, class_info['id'], class_info['title'])

            logging.info(f"章节《{section['name']}》已完成")

    def run(self) -> None:
        """运行自动刷课程序"""
        # 获取用户信息
        response = requests.get('https://changjiang.yuketang.cn/v2/api/web/userinfo', headers=self.headers).text

        # 获取课程列表
        response = requests.get('https://changjiang.yuketang.cn/v2/api/web/courses/list?identity=2',
                              headers=self.headers).json()
        
        if response['errmsg'] != 'Success':
            logging.error("认证失败：csrftoken或sessionid无效")
            return

        # 显示课程列表
        course_list = response['data']['list']
        for index, course in enumerate(course_list):
            print(f"编号：{index + 1} 课名：{course['course']['name']}")

        # 选择课程
        print("\n请选择要刷的课程编号：")
        number = 1
        cid = str(course_list[number - 1]['classroom_id'])

        # 获取课程活动
        url = f'https://changjiang.yuketang.cn/v2/api/web/logs/learn/{cid}?actype=-1&page=0&offset=30&sort=-1'
        response = requests.get(url, headers=self.headers).json()

        import pprint
        pprint.pprint(response)

        if response['data']['prev_id'] == -1:
            logging.warning('该课程暂无内容，程序退出')
            return

        if response['errcode'] != 0:
            logging.error(f'获取课程活动失败：{response}')
            return

        # 处理课程活动
        courseware_ids = []
        chapter_map = {}
        
        for activity in response['data']['activities']:
            if activity['type'] != 15:
                continue
                
            courseware_ids.append(activity['courseware_id'])
            chapter_map[activity['courseware_id']] = activity['title']

            # 更新请求头
            self.headers['classroom-id'] = cid
            self.headers['xtbz'] = 'ykt'
            self.headers['Referer'] = f'https://changjiang.yuketang.cn/v2/web/studentLog/{cid}'

            # 获取课程详细信息
            data = {'cid': cid, 'new_id': courseware_ids}
            response = requests.post('https://changjiang.yuketang.cn/mooc-api/v1/lms/learn/course/pub_new_pro',
                                   headers=self.headers, data=json.dumps(data)).json()

            # 处理每个课件
            for courseware_id in response['data']:
                url = f'https://changjiang.yuketang.cn/c27/online_courseware/xty/kls/pub_news/{courseware_id}/'
                ret = requests.get(url, headers=self.headers).json()
                
                if ret['success'] == 'False':
                    logging.error(f'获取课程数据失败：{ret}')
                    return
                
                self.process_course_content(ret['data']['content_info'], cid)

if __name__ == "__main__":
    automation = YuKeTangAutomation()
    automation.run()
