from django import forms
from django.utils.translation import ugettext_lazy as _

from pgm4app.models import Content, Tag


class AskForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Textarea(
            attrs={'placeholder': _('Explain or add more details (optional)')})
        self.fields['text'].label = ''

        self.fields['title'].widget = forms.Textarea(
            attrs={'placeholder': self.fields['title'].label})
        self.fields['title'].label = ''

        self.fields['tags'].widget = forms.CheckboxSelectMultiple()
        self.fields['tags'].label = ''
        self.fields['tags'].queryset = Tag.objects.all()

    class Meta:
        fields = ['title', 'text', 'tags']
        model = Content


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['text']

