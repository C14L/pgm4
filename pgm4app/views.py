from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from pgm4app.forms import AskForm
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


class QuestionListView(ListView):
    queryset = Content.objects.public().questions()
    template_name = 'pgm4app/question_list.html'


class QuestionDetailView(DetailView):
    queryset = Content.objects.public().questions()
    template_name = 'pgm4app/question_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'


class AskView(FormView):
    template_name = 'pgm4app/ask.html'
    form_class = AskForm

    def get_success_url(self):
        return reverse('question-list')
        # 'question-detail', args=[self.pk, self.slug])

    def form_valid(self, form):
        return super().form_valid(form)
