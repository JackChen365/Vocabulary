# Create your tests here.
import collections
import json
import os
import re

import requests
from bs4 import BeautifulSoup
from nltk import WordNetLemmatizer

from app.dict.query.mdict_query import IndexBuilder

lemmatizer = WordNetLemmatizer()
# 如果不提供第二个参数，单词变体还原为名词
# pythonly 无法还原，说明精确度仍然达不到100%
from nltk.stem.wordnet import WordNetLemmatizer

lmtzr = WordNetLemmatizer()

"""
    生成自有词库，词源信息，从Macmillan中取，中文释义，从柯林期词获取，图片从百词斩取
"""


class WordItem(object):
    """单词信息"""

    def __init__(self, name):
        self.word = name
        self.uk_sound = None
        self.us_sound = None
        self.uk_phonetic = None
        self.us_phonetic = None
        self.pic = ""
        self.tv = ""
        self.star = "☆☆☆"
        self.description = ""  # 主要解释
        self.description_html = []  # 所有解释的html信息
        self.cn = ""  # 中文释义
        self.part_list = []
        self.part_main = []

    def __str__(self):
        return "%s %s %s\n%s\n%s\n%s" % (
            self.word, self.uk_phonetic, self.us_phonetic, self.uk_sound, self.us_sound, self.description)

    def is_valid(self):
        return self.uk_phonetic is not None and self.us_phonetic is not None and self.uk_sound is not None and self.us_sound is not None


def query_word_doc(index_builder, word):
    # 提取网页内单词名称正则，用以校验多个翻译文本时，哪个为解释文本，哪个为外链介绍
    rs = index_builder.mdx_lookup(word)
    doc = None
    if 1 == len(rs):
        # 只有一个词条
        doc = rs[0].strip()
    elif 1 < len(rs):
        if not doc:
            doc = rs[-1]
    else:
        doc = None
    return doc


def _query_desc_items(word, out):
    """查找单词解释信息"""
    team_items = re.compile(r"<b>\d+.</b></font>(.+?)<br>").findall(out)
    if 0 == len(team_items):
        # 如果没有分组信息
        items = []
        summary_matcher = re.compile("<font color=\"#019444\"><i><font>Summary</font></i></font>").search(out)
        if summary_matcher is not None:
            pass
        # 总结性片断，忽略
        # print("\t%s Summery chapter!" % word)
        else:
            matcher = re.compile(r"<br>(.+?)<br>").search(out)
            if matcher is not None:
                # 记录结果
                items.append(matcher.group(1))
        return items
    else:
        # 如果存在分组
        return team_items


def analysis(item, doc):
    result_dict = {}
    """分析单词信息"""
    word_item = WordItem(item)
    pattern = re.compile(
        r"(?=<b>(<font>)?(?P<name>[^<]+)(</font>)?</b>|"
        r"<b><font color=\"#b904af\">▪ <font>I+.</font></font>\s?(<font>)?(?P<name1>[^<]+)(</font>)?</b>)")
    matcher = pattern.search(doc)
    if matcher is not None:
        result_dict.setdefault("name", 0)
        result_dict["name"] += 1
    else:
        result_dict.setdefault("un_name", 0)
        result_dict["un_name"] += 1
    # 测试提取uk音标
    uk_phonetic_pattern = re.compile(
        r"<font color=\"#ff5400\">UK</font>\s<a href=\"sound://(?P<uk_sound>[^\"]+)\">"
        r"<img[^>]+></a>\s?<font color=\"#21887d\">\[(?P<uk_phonetic>[^\]]+)\]</font>")
    matcher = uk_phonetic_pattern.search(doc)
    if matcher is not None:
        word_item.uk_sound = matcher.group("uk_sound")
        word_item.uk_phonetic = matcher.group("uk_phonetic")
        result_dict.setdefault("uk_phonetic", 0)
        result_dict["uk_phonetic"] += 1
    else:
        result_dict.setdefault("un_uk_phonetic", 0)
        result_dict["un_uk_phonetic"] += 1
    # # 测试提取us音标
    us_phonetic_pattern = re.compile(
        r"<font color=\"#ff5400\">US</font>\s<a href=\"sound://(?P<us_sound>[^\"]+)\">")
    matcher = us_phonetic_pattern.search(doc)
    if matcher is not None:
        word_item.us_sound = matcher.group("us_sound")
        us_phonetic_pattern = re.compile(r"<font color=\"#ff5400\">US</font>\s<a href=\"([^\"]+)\">"
                                         r"<img[^>]+></a>\s?<font color=\"#21887d\">\[(?P<us_phonetic>[^\]]+)\]</font>").search(
            doc)
        # 美式单独检测，因为可能与英式一致
        if us_phonetic_pattern is not None:
            word_item.us_phonetic = us_phonetic_pattern.group("us_phonetic")
        result_dict.setdefault("us_phonetic", 0)
        result_dict["us_phonetic"] += 1
    else:
        result_dict.setdefault("un_us_phonetic", 0)
        result_dict["un_us_phonetic"] += 1
    # 测试提取星级 <font color="#ff5400">★★</font>
    star_pattern = re.compile(r"<font color=\"#ff5400\">(?P<star>★+)</font>")
    matcher = star_pattern.search(doc)
    if matcher is not None:
        result_dict.setdefault("star", 0)
        result_dict["star"] += 1
        word_item.star = matcher.group("star").ljust(3, "☆")
    else:
        result_dict.setdefault("un_star", 0)
        result_dict["un_star"] += 1
    # #取解释
    # 检测是否存在大分层
    level_items = re.compile(r"<b><font color=\"#b904af\">▪ <font>[VI]+\.</font></font>").findall(doc)
    item_level = len(level_items)
    result_dict.setdefault(item_level, 0)
    result_dict[item_level] += 1
    # 记录解释信息
    desc_items = collections.OrderedDict()
    if 0 == item_level:
        # 记录子解释个数
        query_desc_items = _query_desc_items(item, doc)
        if 0 < len(query_desc_items):
            desc_items.setdefault(0, [])
            desc_items[0] = query_desc_items
    elif 1 <= item_level:
        # 多级的
        level_items = re.compile(r"<b><font color=\"#b904af\">▪ <font>[VI]+\.</font></font>").split(doc)
        # 过滤空信息
        level_items = list(filter(lambda x: 0 != len(x.strip()), level_items))
        level = 0
        for level_item in level_items:
            # 记录子解释个数
            query_desc_items = _query_desc_items(item, level_item)
            desc_items.setdefault(level, [])
            desc_items[level] = query_desc_items
            level += 1
    # 拼装描述信息html
    # word_item.desc_items = desc_items
    levels = ["I", "II", "III", "IV", "V", "VI", "VII", "V"]
    for items in desc_items.values():
        if items:
            word_item.description_html.append(items)
    # 记录主要解释信息，取第一条
    for level, items in desc_items.items():
        if 0 != len(items):
            word_item.description = items[0]
            break

    # 如果美式音标为空，则美式与英文一致
    if word_item.us_phonetic is None:
        word_item.us_phonetic = word_item.uk_phonetic
    return word_item


def read_mac_info(index_builder, count_dict, key):
    doc = query_word_doc(index_builder, key)
    word_item = None
    if not doc:
        print("word:%s doc is valid" % key)
    else:
        word_item = analysis(key, doc)
        if not word_item.is_valid():
            count_dict["in_valid_count"] += 1
        else:
            count_dict["valid_count"] += 1
    return word_item


def read_bai_info(word_item, key):
    folder_path = "D:\\Dict\\Baicizhan"
    if not os.path.exists(os.path.join(folder_path, "_" + key)):
        pass
    else:
        with open(os.path.join(folder_path, "_" + key), "r", encoding="utf-8") as f:
            text = f.read()
            if text and text.strip():
                query_data = json.loads(text)
                word_item.pic = query_data.get("img")
                word_item.tv = query_data.get("tv")


def read_co_info(index_builder, count_dict, word_item, key):
    doc_items = index_builder.mdx_lookup(key)
    if 0 == len(doc_items):
        count_dict["co_count1"] += 1
    else:
        bs = BeautifulSoup(doc_items[0], "html.parser")
        tab_content = bs.select(".tab_content")
        part_list1 = bs.select(".part_list ol li")
        part_list3 = bs.select(".part_main")
        for part_item in part_list3:
            find_items = part_item.find_all("div", attrs={"class": "collins_en_cn"})
            part_items = []
            word_item.part_main.append(part_items)
            for find_item in find_items:
                if find_item.div:
                    span_items = find_item.div.find_all("span")[:3]
                    text = "".join([item.prettify() for item in span_items])
                    if text.strip():
                        part_items.append(text)
        part_count = len(part_list3) + (1 if part_list1 else 0)
        if tab_content:
            try:
                content_len = len([item for item in tab_content[0].contents if item.__str__().strip()])
                assert content_len == part_count
            except AssertionError:
                print("AssertionError:%s" % key)
        if len(word_item.part_main):
            count_dict["co_count5"] += 1


def save_resource_file(dict_builder, file_path, res):
    # 数据索引内格式为\分隔，所有必须转，否则查找数据时会失效
    result = True
    bytes_list = dict_builder.mdd_lookup("\\" + res.replace("/", "\\"))
    if 0 == len(bytes_list):
        result = False
        print("\t资源:%s查询失败!" % res)
    else:
        # 因为部分资源为img/xx.jpg 所有需要取具体名称
        with open(file_path, 'wb') as f:
            f.write(bytes_list[0])
    return res, result


def download(file_path, url, failure_retry=True):
    file_name = os.path.basename(url)
    try:
        with open(os.path.join(file_path, file_name), "wb") as f:
            f.write(requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36'
            }).content)
    except Exception:
        # 失败重试
        if failure_retry:
            print("\tfile:%s download failure，retry!" % file_name)
            return download(url, file_path, False)
        else:
            print("\tfile:%s download failure!" % file_name)


def read_word_items():
    index_builder = IndexBuilder("../static/dict/Macmillan.mdx")
    cobuild_index_builder = IndexBuilder("../static/dict/柯林斯COBUILD高阶英汉双解学习词典.mdx")
    keys = index_builder.get_mdx_keys()
    # keys = ["close"]
    result_items = []
    count_dict = {"in_valid_count": 0,
                  "valid_count": 0,
                  "co_count1": 0,
                  "co_count2": 0,
                  "co_count3": 0,
                  "co_count4": 0,
                  "co_count5": 0,
                  }
    run_count = 0
    for key in keys:
        word_item = read_mac_info(index_builder, count_dict, key)
        if word_item and word_item.is_valid():
            read_bai_info(word_item, key)
            read_co_info(cobuild_index_builder, count_dict, word_item, key)
            result_items.append(word_item)
        run_count += 1
        if run_count % 1000 == 0:
            print("current:%d" % run_count)
    file_path = "D:\\Dict"
    # 保存音频
    # run_count = 0
    # for word_item in result_items:
    #     # uk
    #     uk_path = os.path.join(file_path, word_item.uk_sound)
    #     if not os.path.exists(uk_path):
    #         save_resource_file(index_builder, uk_path, word_item.uk_sound)
    #     # us
    #     us_path = os.path.join(file_path, word_item.us_sound)
    #     if not os.path.exists(us_path):
    #         save_resource_file(index_builder, us_path, word_item.us_sound)
    #     # img
    #     if word_item.pic:
    #         pic_path = os.path.join(file_path, word_item.pic)
    #         if not os.path.exists(pic_path):
    #             download(file_path, word_item.pic, True)
    #     # tv
    #     if word_item.tv:
    #         tv_path = os.path.join(file_path, word_item.tv)
    #         if not os.path.exists(tv_path):
    #             download(file_path, word_item.tv, True)
    #     run_count += 1
    #     if run_count % 1000 == 0:
    #         print("current:%d" % run_count)
    pic_items = [item for item in result_items if item.pic]
    print(len(pic_items))
    with open(os.path.join(file_path, "history.json"), 'w', encoding="utf-8") as outfile:
        json_string = json.dumps([ob.__dict__ for ob in result_items])
        outfile.write(json_string)
    print("total:%d" % len(keys))
    print(count_dict)


read_word_items()
