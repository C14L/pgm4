from django import forms

from pgm4app.models import Content, Tag


class AskForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].widget = forms.CheckboxSelectMultiple()
        self.fields['tags'].queryset = Tag.objects.all()

    class Meta:
        fields = ['title', 'text', 'tags']
        model = Content


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['text']

