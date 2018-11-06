import os

from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver


class ImportSession(models.Model):
    """一批导入集"""
    export_id = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    # 任务处理状态
    finished = models.BooleanField(default=False)
    ct = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "系列记录:%s[%s]" % (self.title, self.export_id)

    class Meta:
        ordering = ["title"]
        verbose_name = "导入系列"
        verbose_name_plural = "导入系列"


class ImportSessionFile(models.Model):
    """导入分析集"""
    session = models.ForeignKey(ImportSession, related_name="session_files", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    file = models.FileField(upload_to='session/')
    used = models.BooleanField(default=False)
    ct = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "记录文件:%s" % self.name

    class Meta:
        ordering = ["ct"]
        verbose_name = "导入文件"
        verbose_name_plural = "导入文件"


@receiver(models.signals.post_delete, sender=ImportSessionFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(models.signals.pre_save, sender=ImportSessionFile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_instance = ImportSessionFile.objects.get(pk=instance.pk)
    except ImportSessionFile.DoesNotExist:
        return False
    else:
        if 0 < len(old_instance.file.name) and not old_instance.file == instance.file:
            if os.path.isfile(old_instance.file.path):
                os.remove(old_instance.file.path)


class SessionSentence(models.Model):
    """分析集句子"""
    index = models.IntegerField()
    session = models.ForeignKey(ImportSession, related_name="session_sentences", on_delete=models.CASCADE)
    session_file = models.ForeignKey(ImportSessionFile, related_name="session_file_sentences", on_delete=models.CASCADE)
    sentence = models.CharField(max_length=1024)
    # 句子单词原型
    sentence_prototype = models.CharField(max_length=1024)
    time = models.CharField(max_length=16, null=True, blank=True)
    note = models.CharField(max_length=1024, null=True, blank=True)
    ct = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s-%s" % (self.sentence, self.note)

    class Meta:
        ordering = ["ct"]
        verbose_name = "材料句子"
        verbose_name_plural = "材料句子"


class SessionWord(models.Model):
    """分析集句子"""
    session = models.ForeignKey(ImportSession, related_name="session_words", on_delete=models.CASCADE)
    word = models.CharField(max_length=128)
    frequency = models.IntegerField(default=0)
    ct = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s[%d]" % (self.word, self.frequency)

    class Meta:
        ordering = ["ct"]
        verbose_name = "材料单词"
        verbose_name_plural = "材料单词"
