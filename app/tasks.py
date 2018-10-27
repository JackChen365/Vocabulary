# Create your tasks here
from __future__ import absolute_import, unicode_literals

import os

from celery import shared_task
from django.contrib.auth.models import User
from django.core.files import File

from app.analysis.analyzer import Analyzer
from app.models import HighFrequencyWord, Vocabulary
from app.session.models import ImportSession, SessionSentence, SessionWord
from app.user.models import ImportRecord, UserVocabulary


@shared_task
def upload_task(user_id, record_id):
    """碰撞单词任务"""
    # 分析文件
    try:
        record = ImportRecord.objects.get(id=record_id)
    except ImportRecord.DoesNotExist:
        print("任务:%s 任务己移除！" % record_id)
    else:
        from app.views import get_analyzer
        analyzer = get_analyzer(record.export_file.path)
        note = ""
        if analyzer is None:
            note = "暂不支持此格式！"
        else:
            # 分析srt文件,并返回查询结果
            """查询生词"""
            query_items = analyzer.get_data()
            # 开始处理数据
            if 0 == len(query_items):
                note = "没有需要分析的单词！"
            else:
                # 解析出当前用户不熟悉生词
                unknown_items = []
                if record.unknown_file is not None:
                    try:
                        with (open(record.unknown_file.path, encoding="utf-8")) as f:
                            for line in f.readlines():
                                unknown_items.append(line.strip())
                    except Exception as e:
                        note += "分析未知文件异常:%d\n"
                        note += "%s\n" % repr(e)
                save_count = 0
                user = User.objects.get(id=user_id)
                vocabulary_set = Vocabulary.objects.all()
                user_vocabulary_set = UserVocabulary.objects.filter(user=user).all()
                for item in query_items:
                    # 不存在则创建
                    if item.name not in unknown_items and not user_vocabulary_set.filter(word=item.name).exists():
                        try:
                            vocabulary_item = vocabulary_set.get(word=item.name)
                        except Vocabulary.DoesNotExist:
                            pass
                        else:
                            UserVocabulary.objects.create(word=vocabulary_item.word,
                                                          word_item=vocabulary_item,
                                                          user=user)
                        save_count += 1
        record.note = note
        record.finished = True
        record.save()
        print("上传任务操作完成!")


@shared_task
def session_task(export_id):
    """处理文件系列"""
    # 加入异步处理任务
    try:
        session_item = ImportSession.objects.get(export_id=export_id)
    except ImportSession.DoesNotExist:
        print("export_id：%s任务己移除!")
    else:
        if not session_item.finished:
            print("开始进行异步操作:%s" % session_item.export_id)
            print(session_item)
            query_items = []
            sentence_dict = {}
            session_files = session_item.session_files.all()
            print("开始处理文件:%d个" % len(session_files))
            for session_file in session_files:
                from app.views import get_analyzer
                analyzer = get_analyzer(session_file.file.path)
                # 1:将单个文件句子进行整合
                sentence_items = analyzer.get_sentence()
                print("文件:%s 获得处理行:%d" % (session_file.file, len(sentence_items)))
                # 2:分词处理
                sentence_dict[session_file] = Analyzer.tokenizer_sentence(query_items, sentence_items, session_file)
            # 3 插入所有文章句子
            insert_count = 0
            session_sentence_items = []
            for sentence_items in sentence_dict.values():
                for sentence_item in sentence_items:
                    sentence_word = " ".join([item.name for item in sentence_item.word_items])
                    session_sentence_items.append(SessionSentence(index=sentence_item.index,
                                                                  session=session_item,
                                                                  session_file=sentence_item.session_file,
                                                                  sentence=sentence_item.sentence,
                                                                  sentence_prototype=sentence_word,
                                                                  time=sentence_item.time,
                                                                  note=sentence_item.note))
                    insert_count += 1
                    if 0 == insert_count % 100:
                        print("当前插入:%d 个句子信息" % insert_count)
            SessionSentence.objects.bulk_create(session_sentence_items)
            insert_count = 0
            sentence_words = []
            for word_item in query_items:
                sentence_words.append(SessionWord(session=session_item,
                                                  word=word_item.name,
                                                  frequency=word_item.count))
                insert_count += 1
                if 0 == insert_count % 100:
                    print("当前插入:%d 个单词信息" % insert_count)
            SessionWord.objects.bulk_create(sentence_words)
            session_item.finished = True
            session_item.save()
            print("系列分析操作完成!")
