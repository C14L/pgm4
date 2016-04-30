from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.db.models import Count, When, Case, Q
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


class Tag(models.Model):
    name = models.CharField(
        max_length=30, blank=False, null=False, editable=True,
        verbose_name='tag',
        help_text=_('A tag has only letters or numbers.'),
        error_messages={'blank': _('Please write a question.')})
    slug = models.SlugField(
        max_length=30, null=False, blank=True, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


def validate_is_question(value):
    if not value.endswith('?'):
        raise ValidationError(_('That is not a question.'))


content_type_choices = (('q', 'question'), ('a', 'answer'), ('c', 'comment'))


class ContentQuerySet(models.QuerySet):

    def questions(self):
        return self.filter(content_type='q')

    def answers(self):
        return self.filter(content_type='a')

    def comments(self):
        return self.filter(content_type='c')

    def public(self):
        return self.filter(is_hidden=False, is_deleted=False)

    def hidden(self):
        return self.filter(is_hidden=True)

    def deleted(self):
        return self.filter(is_deleted=True)

    def viewable_only(self, user):
        """
        Return all questions except for hidden/deleted not written by user
        :param user:
        """
        return self.filter(Q(user=user) |
                           Q(is_hidden=False) | Q(is_deleted=False))

    def tagged(self, tag_slug):
        """
        Return only questions tagged with this tag.
        :param tag_slug:
        :return:
        """
        return self.filter(tag__slug=tag_slug)

    def without_children(self):
        return self.annotate(count=Count('children')).filter(count=0)

    def with_children(self):
        return self.annotate(count=Count('children')).filter(count__gt=0)

    def questions_with_answers(self):
        return self.all().public().questions().with_children()

    def questions_without_answers(self):
        return self.all().public().questions().without_children()

    def questions_without_accepted_answer(self):
        return self.all().public().questions().annotate(
            count=Count(Case(When(children__is_accepted=True, then=1),
            output_field=models.IntegerField()))).filter(count__gt=0)


class Content(models.Model):

    content_type = models.CharField(
        max_length=1, choices=content_type_choices, null=False, editable=False)
    slug = models.SlugField(
        null=False, blank=True, default='')
    title = models.CharField(
        max_length=200, blank=False, null=False, editable=True,
        verbose_name='question',
        help_text=_('Please write a question.'),
        error_messages={'blank': _('Please write a question.')})
    text = models.TextField(
        max_length=100000, blank=True, null=False, editable=True, default='',
        verbose_name='')
    ip = models.GenericIPAddressField(blank=True, null=True, default=None,
                                      editable=False)
    parent = models.ForeignKey(
        'self', models.SET_NULL, related_name='children',
        null=True, default=None, editable=False)
    user = models.ForeignKey(
        User, models.SET_NULL, related_name='own_content',
        null=True, default=None, editable=False)
    tags = models.ManyToManyField(
        Tag, related_name='content', editable=True)

    is_hidden = models.BooleanField(default=False, editable=False)  # by user
    is_deleted = models.BooleanField(default=False, editable=True)  # by admin
    is_accepted = models.BooleanField(default=False, editable=True)  # by asker

    created = models.DateTimeField(null=False, editable=False, default=now)
    up = models.PositiveIntegerField(null=False, editable=True, default=0)
    down = models.PositiveIntegerField(null=False, editable=True, default=0)
    points = models.PositiveIntegerField(null=False, editable=True, default=0)
    timepoints = models.BigIntegerField(null=False, editable=False, default=0)

    objects = ContentQuerySet.as_manager()

    class Meta:
        ordering = ['-id', '-created']

    def __str__(self):
        if self.content_type == 'q':
            return 'Question {}: "{}"'.format(self.pk, self.title)
        elif self.content_type == 'a':
            return 'Answer {}'.format(self.pk)
        elif self.content_type == 'c':
            return 'Comment {}'.format(self.pk)
        else:
            return 'Undefined content type {}: "{}"'.format(self.pk, self.title)

    def save(self, *args, **kwargs):
        if self.content_type == 'q':
            self.slug = slugify(self.title)

        if self.content_type == 'a' and self.is_accepted:
            # Make sure there is no other accepted answer for this question.
            if self.parent.children\
                   .filter(is_accepted=True).exclude(pk=self.pk).exists():
                raise IntegrityError("Question can't have more "
                                     "than one accepted answer")
        super().save(*args, **kwargs)

    @classmethod
    def get_content_type_id(cls, name):
        return [a[0] for a in content_type_choices if a[1] == name][0]

    def answers(self, public_only=True):
        if self.content_type == 'q':
            qs = Content.objects.answers()
            if public_only:
                qs = qs.public()
            return qs.filter(parent=self.pk)
        else:
            raise ValueError('Only questions have answers.')

    def comments(self, public_only=True):
        qs = Content.objects.all()

        if self.content_type == 'q':
            qs = qs.questions()
        elif self.content_type == 'a':
            qs = qs.answers()
        else:
            raise ValueError('Only questions and answers have comments.')

        if public_only:
            qs = qs.public()

        return qs.filter(parent=self.pk)
