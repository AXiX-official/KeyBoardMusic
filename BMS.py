import re
from typing import Dict
import pickle
import os


class BMS:
    """
    BMS文件解析类
    """

    __slots__ = ('Bpm', 'info', 'key_type', 'key_dict', 'track', 'max_para', 'm_l', 'file_name')

    def __init__(self, fp, type='wav'):
        # 读取bms文件，获取title，artist，bpm等信息
        self.Bpm = 120
        self.info = dict.fromkeys(('TITLE', 'ARTIST', 'BPM', 'PLAYLEVEL', 'RANK'), )
        self.key_type = 'wav'
        self.key_dict: dict
        self.track: list
        self.max_para = 0
        self.m_l = 0

        self.file_name = os.path.basename(fp).split('.')[0]
        if self.__check_cache():
            # 读取缓存
            obj = BMS.__read4file(self.file_name)
            for key in self.__slots__:
                setattr(self, key, getattr(obj, key))
        else:
            # 读取bms文件
            try:
                with open(fp, 'r', encoding='utf-8') as bms_file:
                    l = bms_file.read()
            except UnicodeDecodeError:
                try:
                    with open(fp, 'r', encoding='gbk') as bms_file:
                        l = bms_file.read()
                except UnicodeDecodeError:
                    exit()
            self.key_type = type
            self.track = []
            # 解析bms文件
            self.__tran(l)
            # 保存缓存
            self.__save2file()

    def __tran(self, raw: str):

        # 获取title等info
        for key in self.info.keys():
            reg = f"#{key} (.*)"
            self.info[key] = re.findall(reg, raw)[0]

        self.Bpm = int(self.info['BPM'])

        # 获取WAV**对应的key音文件
        keys = re.findall(r"#WAV(\w\w) (.*)[.](.*)", raw)
        self.key_dict = dict([(i[0], i[1]) for i in keys])

        # 获取note
        raw_list = re.findall(r"#(\d\d\d)(.*):(.*)", raw)
        raw_list = [(i[0], i[2]) for i in raw_list]
        temp_dict: Dict[int, set] = {}
        for key, value in raw_list:
            key = int(key)
            if key in temp_dict.keys():
                temp_dict[key].add(value)
            else:
                temp_dict[key] = {value}
        self.max_para = list(temp_dict.keys())[-1] + 1
        for i in range(self.max_para):
            if i not in temp_dict.keys():
                temp_dict[i] = set()
        temp_list = [temp_dict[i] for i in range(self.max_para)]
        self.m_l = len(
            max([max(temp_list[i], key=len, default='') for i in range(self.max_para)], key=len, default='')) // 2
        for notes in temp_list:
            ll = [[] for i in range(self.m_l)]
            if notes:
                for n in notes:
                    l = len(n) // 2
                    reg = r"(\w\w)" * l
                    t_l = (re.findall(reg, n)[0])
                    if l == 1:
                        if t_l != '00':
                            ll[0].append(self.key_dict[t_l] + '.' + self.key_type)
                    else:
                        for i in range(0, l):
                            if t_l[i] != '00':
                                try:
                                    ll[i * self.m_l // l].append(self.key_dict[t_l[i]] + '.' + self.key_type)
                                except KeyError:
                                    pass
            self.track.extend(ll)

    def zip(self):
        result = []
        p = iter(self.track)
        t = [next(p), 0]
        temp = None
        while True:
            try:
                temp = next(p)
                if not temp:
                    t[1] += 1
                else:
                    result.append(t)
                    t = [temp, 0]
            except StopIteration:
                break
        return result

    def __save2file(self, fp=r'./'):
        with open(os.path.join(fp, self.file_name + '_bms'), 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def __read4file(cls, fn: str, fp=r'./'):
        with open(os.path.join(fp, fn + '_bms'), 'rb') as f:
            return pickle.load(f)

    def __check_cache(self, fp=r'./'):
        if os.path.exists(os.path.join(fp, self.file_name + '_bms')):
            return True
        else:
            return False
