import re

import nltk
from nltk.tokenize import word_tokenize
from app.analysis.analyzer import Analyzer, QueryItem, QuerySentence


class LrcAnalyzer(Analyzer):
    """音频lrc文件分析器"""

    def __init__(self, file_path):
        if not file_path.endswith("lrc"):
            raise Exception("file is not lrc!")
        self.file_path = file_path

    def stem_item(self, item):
        p = nltk.PorterStemmer()
        return p.stem(item.lower())

    def resolve_lrc(self):
        """解析lrc文件"""
        items = []
        # 00:41:29,840 --> 00:41:29,840
        pattern = re.compile("(?P<time>\[.+?\])(?P<en>[\x00-\x7F]+)?\s?(?P<cn>.+)?")
        encoding = self.get_encoding(self.file_path)
        with open(self.file_path, 'r', encoding=encoding, errors='ignore') as f:
            for line in f.readlines():
                if line.strip():
                    matcher = pattern.search(line.strip())
                    if matcher:
                        en = matcher.group("en")
                        if en and en.strip():
                            items.append(QuerySentence(matcher.group("en"), matcher.group("cn"), matcher.group("time")))
        return items

    def get_data(self):
        items = self.get_sentence()
        # 分词处理
        return self.tokenizer(items)

    def get_sentence(self):
        return self.resolve_lrc()
