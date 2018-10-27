from django.contrib.auth.models import User
from django.db import models


class QueryDictFile(models.Model):
    """查询字典文件"""
    mdx_file = models.FileField(verbose_name="字典文件", upload_to="dict/")
    mdd_file = models.FileField(verbose_name="数据文件", upload_to="dict/")
    mdx_md5 = models.CharField(verbose_name="md5", max_length=64)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return self.mdx_file.name

    class Meta:
        ordering = ["ct"]
        verbose_name = "字典文件"
        verbose_name_plural = "字典文件"


class UserQueryDict(models.Model):
    """查询字典文件"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dict_name = models.CharField(verbose_name="字典名称", max_length=64)
    dict_file = models.ForeignKey(QueryDictFile, verbose_name="字典文件", on_delete=models.CASCADE)
    position = models.IntegerField("排序位置")
    up = models.DateTimeField("更新时间", auto_now_add=True)
    ct = models.DateTimeField("记录时间", auto_now_add=True)

    def __str__(self):
        return self.dict_file.__str__()

    class Meta:
        ordering = ["ct"]
        verbose_name = "查询字典"
        verbose_name_plural = "查询字典"



