from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'title',
                'aria-describedby': 'titleFeedback',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'id': 'description',
                'aria-describedby': 'descriptionFeedback',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.errors.get('description'):
            self.fields['description'].widget.attrs.update({'class': 'form-control is-invalid'})
        if self.errors.get('title'):
            self.fields['title'].widget.attrs.update({'class': 'form-control is-invalid'})