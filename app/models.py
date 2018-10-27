import os

from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models


class Vocabulary(models.Model):
    word = models.CharField("单词", unique=True, max_length=128)
    uk_sound = models.FileField(verbose_name="音式发音", upload_to="vocabulary/sound/", null=True, blank=True)
    us_sound = models.FileField(verbose_name="美式发音", upload_to="vocabulary/sound/", null=True, blank=True)
    uk_phonetic = models.CharField("英式音标", max_length=32, null=True, blank=True)
    us_phonetic = models.CharField("美式音标", max_length=32, null=True, blank=True)
    picture = models.ImageField("联想图片", upload_to="vocabulary/picture/", null=True, blank=True)
    star = models.CharField("单词星级", max_length=12)
    high_frequency = models.BooleanField("高频词", default=False)
    en_desc = models.TextField("英文解释")
    cn_desc = models.TextField("中文解释")
    query_count = models.IntegerField("查询次数", default=0)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "%s" % self.word

    class Meta:
        ordering = ["ct"]
        verbose_name = "常用单词"
        verbose_name_plural = "常用单词"


@receiver(models.signals.post_delete, sender=Vocabulary)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.uk_sound:
        if os.path.isfile(instance.uk_sound.path):
            os.remove(instance.uk_sound.path)
    if instance.us_sound:
        if os.path.isfile(instance.us_sound.path):
            os.remove(instance.us_sound.path)
    if instance.picture:
        if os.path.isfile(instance.picture.path):
            os.remove(instance.picture.path)


@receiver(models.signals.pre_save, sender=Vocabulary)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_instance = Vocabulary.objects.get(pk=instance.pk)
    except Vocabulary.DoesNotExist:
        return False
    else:
        if not old_instance.uk_sound == instance.uk_sound:
            if os.path.isfile(old_instance.uk_sound.path):
                os.remove(old_instance.uk_sound.path)
        if not old_instance.us_sound == instance.us_sound:
            if os.path.isfile(old_instance.us_sound.path):
                os.remove(old_instance.us_sound.path)
        if not old_instance.picture == instance.picture:
            if os.path.isfile(old_instance.picture.path):
                os.remove(old_instance.picture.path)


class HighFrequencyWord(models.Model):
    word = models.CharField("单词", unique=True, max_length=128)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return "%s" % self.word

    class Meta:
        ordering = ["ct"]
        verbose_name = "高频单词"
        verbose_name_plural = "高频单词"
