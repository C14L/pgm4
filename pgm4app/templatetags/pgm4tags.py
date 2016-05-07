from django.template.defaultfilters import register

from pgm4app.models import Vote


@register.filter(name='complete_content_list_for_user')
def complete_content_list_for_user(content_list, user):
    """
    :param content_list: A list or queyset of Content objects.
    :param user: A user object who's votes we are looking for.
    :return: List of Content obj. w "is_upvote", "is_downvote" properties added.
    """
    if user.is_anonymous():
        return content_list

    content_list = list(content_list)
    content_id_list = [x.id for x in content_list]
    votes_qs = Vote.objects.filter(user=user, content_id__in=content_id_list)
    votes = {obj.content_id: obj.value for obj in votes_qs}
    for obj in content_list:
        obj.is_upvoted = votes.get(obj.id, 0) == 1
        obj.is_downvoted = votes.get(obj.id, 0) == -1

    return content_list
