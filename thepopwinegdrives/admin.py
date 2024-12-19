from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
from .models import ScrapedContent, Book, Script
from .views import scrape_webpage, fetch_books_view, fetch_file_content_view
from django.template.response import TemplateResponse
from .forms import RunScriptForm
from django.utils import timezone
from django.utils.html import format_html
from celery.app.control import Control
from .models import ClientApp
import secrets
class ScrapeForm(forms.Form):
    url = forms.URLField(widget=forms.URLInput(attrs={'placeholder': 'Enter URL to scrape'}))

class ScrapedContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'created_at')
    search_fields = ('title', 'url')
    list_filter = ('created_at', 'url')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('scrape/', self.admin_site.admin_view(self.scrape_view), name='scrape-content'),
        ]
        return custom_urls + urls

    def scrape_view(self, request):
        if request.method == 'POST':
            form = ScrapeForm(request.POST)
            if form.is_valid():
                url = form.cleaned_data['url']
                title, content = scrape_webpage(url)
                ScrapedContent.objects.create(url=url, title=title, content=content)
                messages.success(request, f'Successfully scraped and saved content from {url}')
                return redirect('admin:thepopwinegdrives_scrapedcontent_changelist')
        else:
            form = ScrapeForm()
        context = dict(
            self.admin_site.each_context(request),
            form=form,
        )
        return render(request, 'admin/scrape_form.html', context)

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'last_accessed')
    search_fields = ('title', 'author')
    list_filter = ('author', 'last_accessed')
    ordering = ('-last_accessed',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch-books/', self.admin_site.admin_view(fetch_books_view), name='fetch-books'),
            path('fetch-file-content/', self.admin_site.admin_view(fetch_file_content_view), name='fetch-file-content'),
        ]
        return custom_urls + urls

    def fetch_books_button(self, request):
        return format_html('<a class="button" href="{}">Fetch Books</a>', reverse('admin:fetch-books'))

    def fetch_file_content_button(self, request):
        return format_html('<a class="button" href="{}">Fetch File Content</a>', reverse('admin:fetch-file-content'))

    change_list_template = "admin/book_change_list.html"

class ScriptAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_running', 'last_run', 'script_actions')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('scripts/', self.admin_site.admin_view(self.scripts_view), name='view-scripts'),
            path('run/', self.admin_site.admin_view(self.run_script_view), name='run-script'),
            path('stop/', self.admin_site.admin_view(self.stop_script_view), name='stop-script'),
        ]
        return custom_urls + urls

    def scripts_view(self, request):
        scripts = Script.objects.all()
        context = {
            'scripts': scripts,
            'opts': self.model._meta,
            'title': 'Scripts',
        }
        return TemplateResponse(request, 'admin/scripts_list.html', context)

    def run_script_view(self, request):
        if request.method == 'POST':
            form = RunScriptForm(request.POST)
            if form.is_valid():
                script_id = form.cleaned_data['script_id']
                script = Script.objects.get(id=script_id)
                # Implement your script running logic here
                script.is_running = True
                script.last_run = timezone.now()
                script.save()
                self.message_user(request, f"Successfully started {script.name}")
                return redirect('admin:view-scripts')
        else:
            form = RunScriptForm()
        context = {
            'form': form,
            'opts': self.model._meta,
            'title': 'Run Script',
        }
        return TemplateResponse(request, 'admin/run_script_form.html', context)

    def stop_script_view(self, request):
        if request.method == 'POST':
            form = RunScriptForm(request.POST)
            if form.is_valid():
                script_id = form.cleaned_data['script_id']
                script = Script.objects.get(id=script_id)
                # Implement your script stopping logic here
                control = Control(app=script.celery_app)
                control.revoke(script.task_id, terminate=True)
                script.is_running = False
                script.save()
                self.message_user(request, f"Successfully stopped {script.name}")
                return redirect('admin:view-scripts')
        else:
            form = RunScriptForm()
        context = {
            'form': form,
            'opts': self.model._meta,
            'title': 'Stop Script',
        }
        return TemplateResponse(request, 'admin/stop_script_form.html', context)

    def script_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Run</a>&nbsp;'
            '<a class="button" href="{}">Stop</a>',
            reverse('admin:run-script', args=[obj.pk]),
            reverse('admin:stop-script', args=[obj.pk])
        )
    script_actions.short_description = 'Actions'
    script_actions.allow_tags = True

@admin.register(ClientApp)
class ClientAppAdmin(admin.ModelAdmin):
    list_display = ['name', 'client_id', 'api_key', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            # If the instance is new, generate a new API key
            obj.api_key = secrets.token_urlsafe(32)
        else:
            # If the name is being changed, ensure it's unique
            if 'name' in form.changed_data:
                if ClientApp.objects.filter(name=obj.name).exists():
                    raise ValueError("A client app with this name already exists.")

        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        # Make the API key read-only after the object has been created
        if obj:  # if obj is not None, this is an existing object
            return ['api_key']
        return []
admin.site.register(Book, BookAdmin)
admin.site.register(ScrapedContent, ScrapedContentAdmin)
admin.site.register(Script, ScriptAdmin)
# admin.site.register(ClientApp)