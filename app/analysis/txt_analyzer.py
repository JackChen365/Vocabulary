import nltk

from app.analysis.analyzer import Analyzer, QuerySentence


class TxtAnalyzer(Analyzer):
    """txt文件分析器"""

    def __init__(self, file_path):
        if not file_path.endswith("txt"):
            raise Exception("file is not txt!")
        self.file_path = file_path

    def stem_item(self, item):
        p = nltk.PorterStemmer()
        return p.stem(item.lower())

    def resolve_txt(self):
        """解析txt文件"""
        items = []
        with open(self.file_path, 'r', errors='ignore') as f:
            for line in f.readlines():
                if line.strip():
                    items.append(QuerySentence(line.strip()))
        return items

    def get_data(self):
        items = self.get_sentence()
        # 分词处理
        return self.tokenizer(items)

    def get_sentence(self):
        return self.resolve_txt()
