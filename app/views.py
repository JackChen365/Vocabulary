import html
import os

from django.http import HttpResponse
# Create your views here.
from django.template import loader

from app.analysis.lrc_analyzer import LrcAnalyzer
from app.analysis.pdf_analyzer import PdfAnalyzer
from app.analysis.srt_analyzer import SrtAnalyzer
from app.analysis.txt_analyzer import TxtAnalyzer
from app.session.models import ImportSession, ImportSessionFile, SessionSentence, SessionWord
from vocabulary.settings import MEDIA_ROOT


def get_analyzer(file_path):
    if file_path.endswith("srt"):
        return SrtAnalyzer(file_path)
    elif file_path.endswith("pdf"):
        return PdfAnalyzer(file_path)
    elif file_path.endswith("lrc"):
        return LrcAnalyzer(file_path)
    elif file_path.endswith("txt"):
        return TxtAnalyzer(file_path)
    else:
        return None


def request_test(request):
    template = loader.get_template('test.html')
    context = {
        "title": "All unknown word",
        "sub_title": "this is file:%s all unknown word!" % "",
    }
    # ImportSession.objects.all().delete()
    # print(ImportSessionFile.objects.all().count())
    # print(SessionSentence.objects.all().count())
    # print(SessionWord.objects.all().count())
    html_text = template.render(context, request)
    return HttpResponse(html.unescape(html_text))


def remote_tmp():
    import shutil
    tmp_path = os.path.join(MEDIA_ROOT, "tmp")
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
