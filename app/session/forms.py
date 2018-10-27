from django import forms

from app.session.models import ImportSessionFile


class ExportSessionForm(forms.ModelForm):
    class Meta:
        model = ImportSessionFile
        fields = ('file', )
