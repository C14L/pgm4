from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.db.models import Count, When, Case, Q, Sum
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


def validate_is_question():
    pass


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


content_type_choices = (('q', 'question'), ('a', 'answer'), ('c', 'comment'))


class ContentQuerySet(models.QuerySet):

    def for_user(self, user):
        """
        # ERROR: this returns one Content object for every related Vote object.
        return self.annotate(
            is_upvoted=Case(When(
                Q(votes__user=user) & Q(votes__value=1), then=True),
                default=False, output_field=models.BooleanField()),
            is_downvoted=Case(When(
                Q(votes__user=user) & Q(votes__value=-1), then=True),
                default=False, output_field=models.BooleanField()))

        # ERROR: This can trivially be converted into is_upvote and is_downvote
        # by looking at num_votes (either 1 or -1) but that would still convert
        # the QS into a list.
        return self.annotate(num_votes=Sum(Case(
                    When(Q(votes__user__pk=1) & Q(votes__value=1), then=1),
                    When(Q(votes__user__pk=1) & Q(votes__value=-1), then=-1),
                    default=0, output_field=models.IntegerField())))
        """
        raise NotImplementedError('Annotate is_upvoted and is_downvoted on the '
                                  'Queryset is not implemented.')

    def questions(self):
        return self.filter(content_type='q').order_by('-timepoints')

    def answers(self):
        return self.filter(content_type='a').order_by('is_accepted',
                                                      '-timepoints')

    def comments(self):
        return self.filter(content_type='c').order_by('id')

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
        # TODO: integrate this into questions() probably as standard and have
        # TODO: a separate all_questions() method to return all, including
        # TODO: hidden and deleted questions.
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
        return self.all().public().questions().annotate(count=Count(Case(
            When(children__is_accepted=True, then=1),
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
        Tag, related_name='content', blank=True, editable=True)

    is_hidden = models.BooleanField(default=False, editable=False)  # by user
    is_deleted = models.BooleanField(default=False, editable=True)  # by admin
    is_accepted = models.BooleanField(default=False, editable=True)  # by asker

    created = models.DateTimeField(null=False, editable=False, default=now)
    up = models.PositiveIntegerField(null=False, editable=True, default=0)
    down = models.PositiveIntegerField(null=False, editable=True, default=0)
    points = models.PositiveIntegerField(null=False, editable=True, default=0)
    timepoints = models.BigIntegerField(null=False, editable=False, default=0)

    count_views = models.PositiveIntegerField(null=False, default=0)
    count_answers = models.PositiveIntegerField(null=False, default=0)
    count_comments = models.PositiveIntegerField(null=False, default=0)
    count_flags = models.PositiveIntegerField(null=False, default=0)
    count_favorite = models.PositiveIntegerField(null=False, default=0)

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
        if self.is_question:
            self.slug = slugify(self.title)

        if self.is_answer and self.is_accepted:
            # Make sure there is no other accepted answer for this question.
            if self.parent.children\
                   .filter(is_accepted=True).exclude(pk=self.pk).exists():
                raise IntegrityError("Question can't have more "
                                     "than one accepted answer")
        super().save(*args, **kwargs)

    @classmethod
    def get_content_type_id(cls, name):
        return [a[0] for a in content_type_choices if a[1] == name][0]

    @property
    def is_question(self):
        return self.content_type == 'q'

    @property
    def is_answer(self):
        return self.content_type == 'a'

    @property
    def is_comment(self):
        return self.content_type == 'c'

    def get_absolute_url(self):
        question = self.get_question()
        return reverse('question-detail', args=[question.pk, question.slug])

    def attach_user_vote(self, user):
        vote = Vote.objects.filter(content=self, user=user).first()
        self.is_upvoted = vote and vote.value == 1
        self.is_downvoted = vote and vote.value == -1

    def count_view(self):
        """Increase the view counter by one."""
        self.count_views += 1
        self.save(update_fields=['count_views'])

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

    def get_question(self):
        """Return the question a Content object is a decendent of."""
        if self.is_question:
            return self
        elif self.is_answer or self.is_comment and self.parent.is_question:
            return self.parent
        elif self.is_comment and self.parent.is_answer:
            return self.parent.parent
        raise IntegrityError('Content object {} is orphan.'.format(self.pk))

    def set_points(self):
        self.points = self.up - self.down

    def set_timepoints(self):
        """
        Use the age and points of an object to calculate a sort order for
        questions and answers. Comments are always shown ordered by age only.
        :return:
        """
        unixtime = self.created.timestamp()  # float
        self.timepoints = unixtime + self.points  # TODO: calc a sort value!

    def _force_vote(self, user, value):
        """User sets vote on this object.
        :param value: either +1 (upvote), -1 (downvote), or 0 (delete vote)
        :param user:
        :return points gained or lost
        """
        previous = 0
        if value == 0:
            # Delete any previous vote object
            for v in Vote.objects.filter(user=user, content=self):
                previous = v.value
                v.delete()
        else:
            # Create or change vote object
            v, created = Vote.objects.get_or_create(user=user, content=self)
            previous = v.value
            v.value = value
            v.save(update_fields=['value'])
        return (previous-value)*(-1)

    def force_upvote(self, user):
        return self._force_vote(user, 1)

    def force_downvote(self, user):
        return self._force_vote(user, -1)

    def delete_vote(self, user):
        return self._force_vote(user, 0)

    def toggle_vote(self, user, value):
        """
        Toggle the vote value. If content item was previously upvoted and gets
        another upvote, the vote is deleted. If content item was previously
        downvoted and gets an upvote, the vote is changed to upvote.
        :param user:
        :param value: must be either 1 (upvote) or -1 (downvote)
        :return:
        """
        try:
            v = Vote.objects.get(user=user, content=self)
        except Vote.DoesNotExist:
            Vote.objects.create(user=user, content=self, value=value)
        else:
            if v.value == value:
                v.delete()
            else:
                v.value = value
                v.save(update_fields=['value'])

        self.up = self.votes.count_upvotes()
        self.down = self.votes.count_downvotes()
        self.set_points()
        self.set_timepoints()
        self.save(update_fields=['up', 'down', 'points', 'timepoints'])


class VoteQuerySet(models.QuerySet):
    def by(self, user):
        return self.filter(user=user)

    def on(self, content):
        return self.filter(content=content)

    def count_upvotes(self):
        """Return the number of actual upvotes."""
        return self.filter(value=1).count()

    def count_downvotes(self):
        """Return the number of actual downvotes."""
        return self.filter(value=-1).count()

    def count_votes(self):
        """Return the sum of upvotes and downvotes."""
        return self.annotate(sum=Sum('value'))


class Vote(models.Model):
    user = models.ForeignKey(
        User, models.CASCADE, related_name='votes', null=False, editable=False)
    content = models.ForeignKey(
        Content, models.CASCADE, related_name='votes', null=False,
        editable=False)
    value = models.SmallIntegerField(null=False, editable=False)

    objects = VoteQuerySet.as_manager()

    class Meta:
        unique_together = (('user', 'content'), )

    def __str__(self):
        return '{} {}: {}'.format(
            self.user.username,
            {'-1': 'downvoted', '1': 'upvoted'}[str(self.value)],
            self.content.title)
