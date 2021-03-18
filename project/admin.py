from django.contrib import admin


class MyAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        if not request.user.is_anonymous:
            context['notifications_count'] = request.user.notifications.unread().count()
        return context
