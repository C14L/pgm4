# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-01 11:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pgm4app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.SmallIntegerField(editable=False)),
            ],
        ),
        migrations.AlterModelOptions(
            name='content',
            options={'ordering': ['-id', '-created']},
        ),
        migrations.AlterField(
            model_name='content',
            name='content_type',
            field=models.CharField(choices=[('q', 'question'), ('a', 'answer'), ('c', 'comment')], editable=False, max_length=1),
        ),
        migrations.AlterField(
            model_name='content',
            name='text',
            field=models.TextField(blank=True, default='', max_length=100000, verbose_name=''),
        ),
        migrations.AlterField(
            model_name='content',
            name='title',
            field=models.CharField(error_messages={'blank': 'Please write a question.'}, help_text='Please write a question.', max_length=200, verbose_name='question'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(blank=True, editable=False, max_length=30),
        ),
        migrations.AddField(
            model_name='vote',
            name='content',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='pgm4app.Content'),
        ),
        migrations.AddField(
            model_name='vote',
            name='user',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='votes', to=settings.AUTH_USER_MODEL),
        ),
    ]