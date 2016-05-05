from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, CreateView, UpdateView, View
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_on_navbar'] = 'profile'
        return context


class TagListView(ListView):
    model = Tag

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_on_navbar'] = 'tags'
        return context


class TagDetailView(DetailView):
    model = Tag

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_on_navbar'] = 'tags'
        return context


class QuestionCreateView(CreateView):
    form_class = AskForm
    template_name = 'pgm4app/question_create.html'

    def get_initial(self):
        # When called with a tags param (e.g. "?tags=sometag+anothertag") then
        # find verify tags exist and pre-select them in the form.
        slug_list = self.request.GET.get('tags', '').split(' ')
        tags = Tag.objects.filter(slug__in=slug_list)
        return {'tags': tags}

    def form_valid(self, form):
        form.instance.content_type = Content.get_content_type_id('question')
        form.instance.user = self.request.user
        form.save()
        messages.success(self.request, _('Your question was published.'))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class QuestionUpdateView(UpdateView):
    model = Content
    form_class = AskForm
    template_name = 'pgm4app/question_create.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, _('Your question was updated.'))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class QuestionListView(ListView):
    template_name = 'pgm4app/question_list.html'

    def _get_order(self):
        order = self.request.GET.get('order', 'hot')
        return order if order in ['hot', 'new', 'top'] else 'hot'

    def get_queryset(self):
        order = self._get_order()
        return Content.objects.public().questions().order(order)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_on_navbar'] = self._get_order()
        return context


class QuestionDetailView(DetailView):
    queryset = Content.objects.public().questions()
    template_name = 'pgm4app/question_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        _object = super().get_object(queryset=queryset)
        _object.attach_user_vote(self.request.user)
        _object.count_view()
        return _object


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


class CommentCreateView(CreateView):
    fields = ['text']
    model = Content
    template_name = 'pgm4app/comment_create.html'
    _parent = None
    _question = None

    def get_parent(self):
        if not self._parent:
            self._parent = get_object_or_404(Content, pk=self.kwargs['parent'])
        return self._parent

    def get_question(self):
        if not self._question:
            self._question = self.get_parent().get_question()
        return self._question

    def form_valid(self, form):
        form.instance.content_type = Content.get_content_type_id('comment')
        form.instance.parent = self.get_parent()
        form.instance.user = self.request.user
        form.save()
        messages.success(self.request, _('Your comment was published.'))
        return super().form_valid(form)

    def get_success_url(self):
        kw = {'pk': self.get_question().pk, 'slug': self.get_question().slug}
        return reverse('question-detail', kwargs=kw)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent'] = self.get_parent()
        context['question'] = self.get_question()
        return context


class CommentUpdateView(UpdateView):
    fields = ['text']
    model = Content
    template_name = 'pgm4app/comment_create.html'
    _question = None

    def get_question(self):
        if not self._question:
            self._question = self.object.get_question()
        return self._question

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, _('Your comment was updated.'))
        return super().form_valid(form)

    def get_success_url(self):
        kw = {'pk': self.get_question().pk, 'slug': self.get_question().slug}
        return reverse('question-detail', kwargs=kw)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent'] = self.object.parent
        context['question'] = self.get_question()
        return context


@method_decorator(login_required, name='dispatch')
class VoteView(View):
    def post(self, *args, **kwargs):
        content = get_object_or_404(Content, pk=kwargs['pk'])
        content.toggle_vote(self.request.user, kwargs['vote'])
        if self.request.is_ajax():
            return JsonResponse({})
        _next = self.request.META.get('HTTP_REFERER', content.get_absolute_url())
        _hash = self.request.POST.get('hash', '')
        _hash = '#{}'.format(_hash) if _hash else ''
        return HttpResponseRedirect(_next + _hash)
