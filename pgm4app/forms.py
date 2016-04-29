from django import forms

from pgm4app.models import Content


class AskForm(forms.ModelForm):

    class Meta:
        model = Content
        fields = ['title', 'text']


class AnswerForm(forms.ModelForm):

    class Meta:
        model = Content
        fields = ['text']

