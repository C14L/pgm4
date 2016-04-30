from django import forms

from pgm4app.models import Content


class AnswerForm(forms.ModelForm):

    class Meta:
        model = Content
        fields = ['text']

