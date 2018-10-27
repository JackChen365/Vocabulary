import re

import nltk
from nltk.tokenize import word_tokenize
from app.analysis.analyzer import Analyzer, QueryItem, QuerySentence


class SrtItem(object):
    def __init__(self, number):
        self.number = number
        self.time = None
        self.sentence = str()


class SrtAnalyzer(Analyzer):
    """视频srt文件分析器"""

    def __init__(self, file_path):
        if not file_path.endswith("srt"):
            raise Exception("file is not srt!")
        self.file_path = file_path

    def stem_item(self, item):
        p = nltk.PorterStemmer()
        return p.stem(item.lower())

    def resolve_srt(self):
        """解析srt文件"""
        items = []
        # 00:41:29,840 --> 00:41:29,840
        with open(self.file_path, 'r', errors='ignore') as f:
            index = 0
            for line in f.readlines():
                srt_l = line.strip()
                if 0 == index:
                    if srt_l:
                        if srt_l.isdigit():
                            item = SrtItem(int(srt_l))
                        else:
                            item = SrtItem(0)
                    else:
                        index = 0
                        continue
                elif 1 == index:
                    start, end = srt_l.split(" --> ")
                    last_number = items[-1].number if 0 < len(items) else -1
                    # 过滤掉无效的字幕信息
                    if start != end and last_number < item.number:
                        items.append(item)
                        item.time = srt_l
                else:
                    if srt_l.strip():
                        item.sentence += srt_l
                    else:
                        index = 0
                        continue
                index += 1
        return items

    def get_data(self):
        items = self.get_sentence()
        # 分词处理
        return self.tokenizer(items)

    def get_sentence(self):
        # 解析文件
        items = self.resolve_srt()
        return [QuerySentence(item.sentence, time=item.time) for item in items]
