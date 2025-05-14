from django import forms

from djangocodemirror.fields import CodeMirrorField, CodeMirrorWidget

class CodeForm(forms.Form):
    code = CodeMirrorField(required=True,
                          config_name="python")