from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, Like


class SearchTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass')
        self.bob = User.objects.create_user(username='bob', password='pass')
        self.carl = User.objects.create_user(username='carl', password='pass')

        # posts
        self.p1 = Post.objects.create(user=self.alice, content='Hello world #greetings')
        self.p2 = Post.objects.create(user=self.bob, content='Another day in paradise')
        self.p3 = Post.objects.create(user=self.bob, content='#greetings Welcome back')

        # likes to make p1 the trending post
        Like.objects.create(user=self.bob, post=self.p1)
        Like.objects.create(user=self.carl, post=self.p1)

    def test_keyword_search(self):
        resp = self.client.get(reverse('search') + '?q=Hello')
        posts = resp.context['posts']
        self.assertIn(self.p1, posts)
        self.assertNotIn(self.p2, posts)

    def test_hashtag_search(self):
        resp = self.client.get(reverse('search') + '?q=%23greetings')
        posts = list(resp.context['posts'])
        self.assertIn(self.p1, posts)
        self.assertIn(self.p3, posts)

    def test_user_search(self):
        resp = self.client.get(reverse('search') + '?q=@bob')
        posts = list(resp.context['posts'])
        self.assertIn(self.p2, posts)
        self.assertIn(self.p3, posts)

    def test_trending_search(self):
        resp = self.client.get(reverse('search') + '?q=trending')
        posts = list(resp.context['posts'])
        # p1 has 2 likes, so it should be first
        self.assertGreater(len(posts), 0)
        self.assertEqual(posts[0], self.p1)

