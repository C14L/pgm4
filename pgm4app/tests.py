from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.text import slugify

from pgm4app.models import Content, Tag


class Pgm4appTestCase(TestCase):
    passwd = 'hunter2'
    user1 = {'username': 'user1', 'password': passwd, 'email': 'jf@example.com'}
    user2 = {'username': 'user2', 'password': passwd, 'email': 'er@example.com'}
    user3 = {'username': 'user3', 'password': passwd, 'email': 'dh@example.com'}

    def setUp(self):
        User.objects.create_user(**self.user1)
        User.objects.create_user(**self.user2)
        User.objects.create_user(**self.user3)

        Tag.objects.create(name='everything')
        Tag.objects.create(name='internet')

    def tearDown(self):
        pass

    def test_login_user(self):
        """
        Verify that anonymous users see a login link and authenticated users
        see a logout link.
        :return:
        """
        page_url = reverse('home')
        login_url = reverse('account_login')

        response = self.client.get(page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, login_url)

        self.client.login(**self.user1)

        response = self.client.get(page_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, login_url)
        self.assertContains(response, self.user1['username'])

    def test_different_users_upvote(self):
        """
        Let user1 create a question, then have user2 and user3 upvote and down-
        vote the question and verify that the votes are counted correctly every
        time. Finally, have user1 delete their question.
        :return:
        """
        # Let user1 create a question
        self.client.login(**self.user1)
        url = reverse('question-create')
        data = {'title': 'What a question?'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        # Verify the question was created and the detail is displayed
        slug = slugify(data['title'])
        pk = Content.objects.get(slug=slug).pk
        self.assertIsInstance(pk, int, msg='pk={} is not int()'.format(pk))
        question_url = reverse('question-detail', args=[pk, slug])
        self.assertRedirects(response, question_url)

        # Verify question content displays, and vote is "0 | 0"
        response = self.client.get(question_url)
        self.assertContains(response, data['title'])
        self.assertContains(response, '"0 | 0"')

        # Have user2 upvote the question
        self.client.login(**self.user2)
        response = self.client.post(reverse('vote-up', args=[pk]), {})
        self.assertRedirects(response, question_url)

        # Verify the question has vote of "1 | 0" displayed.
        response = self.client.get(question_url)
        self.assertContains(response, '"1 | 0"')

        # Have user3 upvote the question, too
        self.client.login(**self.user3)
        response = self.client.post(reverse('vote-up', args=[pk]), {})
        self.assertRedirects(response, question_url)

        # Verify the question has vote of "2 | 0" displayed.
        response = self.client.get(question_url)
        self.assertContains(response, '"2 | 0"')

        # Have user3 downvote the question now, removing previous upvote
        response = self.client.post(reverse('vote-down', args=[pk]), {})
        self.assertRedirects(response, question_url)

        # Verify the question has vote of "1 | 1" displayed.
        response = self.client.get(question_url)
        self.assertContains(response, '"1 | 1"')

        # Have user2 downvote the question now, removing previous upvote
        self.client.login(**self.user2)
        response = self.client.post(reverse('vote-down', args=[pk]), {})
        self.assertRedirects(response, question_url)

        # Verify the question has vote of "0 | 2" displayed.
        response = self.client.get(question_url)
        self.assertContains(response, '"0 | 2"')

    def test_create_question_answer_comments(self):
        """
        Let user1 create a question, user2 create an answer on the question,
        user3 create a comment on the question and a comment on the answer.
        Finally, let user1 hide the question, verify that objects are not
        displayed anymore.
        :return:
        """
        # Let user1 create a question
        self.client.login(**self.user1)
        url = reverse('question-create')
        data = {'title': 'What a question?', 'text': 'jds8 question osyfsh.'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        # Question object exists
        q = Content.objects.get(slug=slugify(data['title']))
        self.assertEqual(q.text, data['text'])

        # Let user2 create an answer
        self.client.login(**self.user2)
        url = reverse('answer-create', args=[q.pk])
        data = {'text': 'uiihdi answer dosyoifu9.'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        # Answer object exists
        a = Content.objects.get(text=data['text'])
        self.assertEqual(a.parent.pk, q.pk)

        # Let user3 create a comment on both question and answer
        self.client.login(**self.user3)
        url_q = reverse('comment-create', args=[q.pk])
        url_a = reverse('comment-create', args=[a.pk])
        data_q = {'text': '90wejgi comment on question pdig9.'}
        data_a = {'text': '64ygfbn comment on answer mqlocic.'}
        response_q = self.client.post(url_q, data=data_q)
        response_a = self.client.post(url_a, data=data_a)
        self.assertEqual(response_q.status_code, 302)
        self.assertEqual(response_a.status_code, 302)

        # Comment objects exist
        c_q = Content.objects.get(text=data_q['text'])
        c_a = Content.objects.get(text=data_a['text'])
        self.assertEqual(c_q.parent.pk, q.pk)
        self.assertEqual(c_a.parent.pk, a.pk)

        # All Content objects' texts are displayed on the question page
        url = reverse('question-detail', args=[q.pk, q.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.text)
        self.assertContains(response, a.text)
        self.assertContains(response, c_q.text)
        self.assertContains(response, c_a.text)

        # Let user1 delete the question
        # TODO

        # Verify that question and decendents are not displayed anymore
        # TODO

