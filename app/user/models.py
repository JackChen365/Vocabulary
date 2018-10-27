from django.contrib.auth.models import User
from django.db import models

from app.session.models import ImportSessionFile


class UserVocabulary(models.Model):
    word = models.CharField("单词", unique=True, max_length=128)
    word_item = models.ForeignKey("Vocabulary", related_name="user_vocabulary", on_delete=models.CASCADE)
    query_count = models.IntegerField("查询次数", default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "%s" % self.word

    class Meta:
        ordering = ["ct"]
        verbose_name = "用户词表"
        verbose_name_plural = "用户词表"


class ImportRecord(models.Model):
    """导入词库分析记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    export_file = models.FileField(verbose_name="分析文件", upload_to="export/")
    unknown_file = models.FileField(verbose_name="未知单词文件", upload_to="export/")
    # 任务处理状态
    finished = models.BooleanField(default=False)
    note = models.CharField(max_length=1024)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "词库记录:%s" % self.ct.strftime("%Y%m%d-%H%m")

    class Meta:
        ordering = ["ct"]
        verbose_name = "导入记录"
        verbose_name_plural = "导入记录"


class QueryWordTag(models.Model):
    """查询词标签"""
    tag = models.CharField("标签名称", max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    style = models.TextField("标签样式")
    color = models.CharField("标签颜色", max_length=7, default="#FFFFFF")
    font_color = models.CharField("字体颜色", max_length=7, default="#000000")
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return self.tag

    class Meta:
        ordering = ["ct"]
        verbose_name = "单词标签"
        verbose_name_plural = "单词标签"


class QueryTranslateRecord(models.Model):
    """用户查询句子记录"""
    source = models.CharField("翻译信息", max_length=128)
    target = models.CharField("句子信息", max_length=128, blank=True, null=True)
    uk_phonetic = models.CharField("英式", max_length=128, blank=True, null=True)
    us_phonetic = models.CharField("美式", max_length=128, blank=True, null=True)
    translate = models.TextField("翻译信息", blank=True, null=True)
    frequency = models.IntegerField("查询次数")
    source_from = models.CharField("查询来源", default="inner", max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(QueryWordTag, related_name="tag_query_translate", on_delete=models.CASCADE, blank=True,
                            null=True)
    session_file = models.ForeignKey(ImportSessionFile, on_delete=models.CASCADE, blank=True, null=True)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "%s[%d]" % (self.source, self.frequency)

    class Meta:
        ordering = ["ct"]
        verbose_name = "查询记录"
        verbose_name_plural = "查询记录"


class SentenceRelative(models.Model):
    """用户查询关联例句记录"""
    query_translate = models.ForeignKey(QueryTranslateRecord, verbose_name="查询信息",
                                        related_name="sentence_relative", on_delete=models.CASCADE)
    source = models.CharField("翻译信息", max_length=128)
    target = models.CharField("句子信息", max_length=128)
    resource = models.CharField("来源", max_length=128)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "%s" % self.source

    class Meta:
        ordering = ["ct"]
        verbose_name = "关联句子"
        verbose_name_plural = "关联句子"


class SentenceKeyword(models.Model):
    """用户查询句子词汇记录"""
    query_translate = models.ForeignKey(QueryTranslateRecord, verbose_name="查询信息",
                                        related_name="sentence_keyword", on_delete=models.CASCADE)
    keyword = models.CharField("词汇", max_length=128)
    info = models.CharField("解释", max_length=128)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "%s" % self.keyword

    class Meta:
        ordering = ["ct"]
        verbose_name = "关联词"
        verbose_name_plural = "关联词"
