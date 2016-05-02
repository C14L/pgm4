from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase


class Pgm4appTestCase(TestCase):
    passwd = 'hunter2'
    user1 = {'username': 'user1', 'password': passwd, 'email': 'jf@example.com'}
    user2 = {'username': 'user2', 'password': passwd, 'email': 'er@example.com'}
    user3 = {'username': 'user3', 'password': passwd, 'email': 'dh@example.com'}

    def setUp(self):
        User.objects.create_user(**self.user1)
        User.objects.create_user(**self.user2)
        User.objects.create_user(**self.user3)

    def tearDown(self):
        pass

    def test_login_user(self):
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

    def test_different_users_vote(self):
        pass