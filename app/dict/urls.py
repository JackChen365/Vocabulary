from django.conf.urls import url

from app.dict.views import QueryWordView, UploadDictView, dict_sort

urlpatterns = [
    url('^query/word/$', QueryWordView.as_view(), name="dict-query-word"),
    url('^upload/file/$', UploadDictView.as_view(), name="dict-upload-file"),
    url('^sort/item/$', dict_sort, name="dict-sort-item"),
]