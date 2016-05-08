from django import forms
from django.utils.translation import ugettext_lazy as _

from pgm4app.models import Content, Tag


class AskForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].widget = forms.Textarea(
            attrs={'placeholder': self.fields['title'].label,
                   'class': 'no-newlines content-title'})
        self.fields['title'].label = ''

        self.fields['text'].widget = forms.Textarea(
            attrs={'placeholder': _('Explain or add more details (optional)'),
                   'class': 'content-text'})
        self.fields['text'].label = ''

        self.fields['tags'].widget = forms.CheckboxSelectMultiple()
        self.fields['tags'].label = ''
        self.fields['tags'].queryset = Tag.objects.all()

    class Meta:
        fields = ['title', 'text', 'tags']
        model = Content


class AnswerForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Textarea(
            attrs={'placeholder': _('Write your answer here'),
                   'class': 'content-text'})

    class Meta:
        model = Content
        fields = ['text']


class CommentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Textarea(
            attrs={'placeholder': _('Write a comment here'),
                   'class': 'no-newlines content-text'})

    class Meta:
        model = Content
        fields = ['text']
