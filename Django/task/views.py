from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.


class IndexView(TemplateView):
    template_name = 'task/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data()

        context['room_name'] = 'bobiks'

        return context


