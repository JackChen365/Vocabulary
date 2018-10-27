import re

import nltk
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO
from io import open

from app.analysis.analyzer import Analyzer, QueryItem, QuerySentence


class PdfAnalyzer(Analyzer):

    def __init__(self, file_path):
        if not file_path.endswith("pdf"):
            raise Exception("file is not pdf!")
        self.file_path = file_path

    def get_data(self):
        items = self.get_sentence()
        # 分词处理
        return self.tokenizer(items)

    def get_sentence(self):
        """分析pdf,读取出所有txt文本"""
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        process_pdf(rsrcmgr, device, open(self.file_path, 'rb'))
        device.close()
        content = retstr.getvalue()
        retstr.close()
        return [QuerySentence(item) for item in content.split("\n") if item.strip()]
