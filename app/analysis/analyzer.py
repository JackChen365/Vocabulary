import re
from abc import abstractmethod

import nltk


class QuerySentence(object):
    """查询句子"""

    def __init__(self, sentence, note=None, time=None):
        self.sentence = sentence
        self.note = note
        self.time = time


class SentenceItem(object):
    """句子对象"""

    def __init__(self, index, item, file=None, time=None):
        self.index = index
        self.sentence = item.sentence
        self.note = item.note
        self.word_items = []
        self.session_file = file
        self.time = time

    def __str__(self):
        return "%s\n%s" % (self.sentence, self.note)


class QueryItem(object):
    """查询对象"""

    def __init__(self, name, count=0):
        self.name = name
        self.count = count
        self.sentence = []
        self.note = None

    def add_sentence(self, sentence_item):
        filter_items = [item for item in self.sentence if item.sentence.lower() == sentence_item.sentence.lower()]
        if 0 == len(filter_items):
            self.sentence.append(sentence_item)

    def __str__(self):
        return "%s(%d)" % (self.name, self.count | 0)


class Analyzer(object):

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def get_sentence(self):
        pass

    @staticmethod
    def get_wordnet_pos(treebank_tag):
        if treebank_tag.startswith('J'):
            return nltk.corpus.wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return nltk.corpus.wordnet.VERB
        elif treebank_tag.startswith('N'):
            return nltk.corpus.wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return nltk.corpus.wordnet.ADV
        else:
            return nltk.corpus.reader.NOUN

    @staticmethod
    def highlight(sentence, word):
        return sentence.replace(word, "<font color=\"red\">%s</font>" % word)

    @staticmethod
    def lemmatize(item):
        """区分单个单词"""
        lmtzr = nltk.WordNetLemmatizer()
        pattern = re.compile(r"\w+")
        if item.strip():
            tag_items = nltk.pos_tag(nltk.word_tokenize(item))
            if 1 <= len(tag_items):
                """只取第一个单词操作"""
                tab_item = tag_items[0]
                word = lmtzr.lemmatize(tab_item[0].lower(), Analyzer.get_wordnet_pos(tab_item[1]))
                if not word.isdigit() and re.fullmatch(pattern, word) is not None:
                    return QueryItem(word)
        return None

    @staticmethod
    def tokenizer(items):
        """分词"""
        query_items = []
        lmtzr = nltk.WordNetLemmatizer()
        pattern = re.compile(r"\w+")
        for i, item in enumerate(items):
            if item.sentence.strip():
                # 当前句子对象
                sentence_item = SentenceItem(i, item)
                tag_items = nltk.pos_tag(nltk.word_tokenize(item.sentence))
                for tag in tag_items:
                    word = lmtzr.lemmatize(tag[0].lower(), Analyzer.get_wordnet_pos(tag[1]))
                    if not word.isdigit() and re.fullmatch(pattern, word) is not None and 1 < len(word.strip()):
                        filter_items = [item for item in query_items if (item.name == word.lower())]
                        if 0 == len(filter_items):
                            query_item = QueryItem(word.lower())
                            query_items.append(query_item)
                        else:
                            query_item = filter_items[0]
                        # 句子关联单词信息
                        sentence_item.word_items.append(query_item)
                        # 单词关联句子
                        query_item.add_sentence(sentence_item)
                        query_item.count += 1
        return query_items

    @staticmethod
    def tokenizer_sentence(query_items, items, session_file):
        """分词"""
        sentence_items = []
        lmtzr = nltk.WordNetLemmatizer()
        pattern = re.compile(r"\w+")
        for i, item in enumerate(items):
            if item.sentence:
                # 当前句子对象
                sentence_item = SentenceItem(i, item, session_file, item.time)
                sentence_items.append(sentence_item)
                tag_items = nltk.pos_tag(nltk.word_tokenize(item.sentence))
                for tag in tag_items:
                    word = lmtzr.lemmatize(tag[0].lower(), Analyzer.get_wordnet_pos(tag[1]))
                    if not word.isdigit() and re.fullmatch(pattern, word) is not None and 1 < len(word.strip()):
                        filter_items = [item for item in query_items if (item.name == word.lower())]
                        if 0 == len(filter_items):
                            query_item = QueryItem(word.lower())
                            query_items.append(query_item)
                        else:
                            query_item = filter_items[0]
                        # 句子关联单词信息
                        sentence_item.word_items.append(query_item)
                        # 单词关联句子
                        query_item.add_sentence(sentence_item)
                        query_item.count += 1
        return sentence_items
