from django.contrib import admin

from pgm4app.models import Content, Tag, Vote

admin.site.register(Content)
admin.site.register(Tag)
admin.site.register(Vote)
