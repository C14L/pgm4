from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from pgm4app.models import Content, Tag


class HomeView(TemplateView):
    template_name = 'pgm4app/home.html'


class UserListView(ListView):
    model = User


class UserDetailView(DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'


class TagListView(ListView):
    model = Tag


class TagDetailView(DetailView):
    model = Tag


class QuestionCreateView(CreateView):
    fields = ['title', 'text']
    model = Content
    template_name = 'pgm4app/question_create.html'

    def form_valid(self, form):
        form.instance.content_type = Content.get_content_type_id('question')
        form.instance.user = self.request.user
        form.save()
        messages.success(self.request, _('Your question was published.'))
        return super().form_valid(form)

    def get_success_url(self):
        kwargs = {'pk': self.object.pk, 'slug': self.object.slug}
        return reverse('question-detail', kwargs=kwargs)


class QuestionUpdateView(UpdateView):
    fields = ['title', 'text']
    model = Content
    template_name = 'pgm4app/question_create.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, _('Your question was updated.'))
        return super().form_valid(form)

    def get_success_url(self):
        kwargs = {'pk': self.object.pk, 'slug': self.object.slug}
        return reverse('question-detail', kwargs=kwargs)


class QuestionListView(ListView):
    queryset = Content.objects.public().questions()
    template_name = 'pgm4app/question_list.html'


class QuestionDetailView(DetailView):
    queryset = Content.objects.public().questions()
    template_name = 'pgm4app/question_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'


class AnswerCreateView(CreateView):
    fields = ['text']
    model = Content
    template_name = 'pgm4app/answer_create.html'

    def _get_question_object(self):
        pk = self.kwargs['question']
        try:
            return Content.objects.public().questions().get(pk=pk)
        except Content.DoesNotExist:
            raise Http404

    def form_valid(self, form):
        form.instance.content_type = Content.get_content_type_id('answer')
        form.instance.parent = self._get_question_object()
        form.instance.user = self.request.user
        form.save()
        messages.success(self.request, _('Your question is published.'))
        return super().form_valid(form)

    def get_success_url(self):
        kwargs = {'pk': self.object.parent.pk, 'slug': self.object.parent.slug}
        return reverse('question-detail', kwargs=kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self._get_question_object()
        return context


class AnswerUpdateView(UpdateView):
    fields = ['text']
    model = Content
    template_name = 'pgm4app/answer_create.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, _('Your answer was updated.'))
        return super().form_valid(form)

    def get_success_url(self):
        kwargs = {'pk': self.object.parent.pk, 'slug': self.object.parent.slug}
        return reverse('question-detail', kwargs=kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.object.parent
        return context
