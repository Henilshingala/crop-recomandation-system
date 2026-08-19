from django.db import models

class MissingQuestion(models.Model):
    question = models.TextField()
    language = models.CharField(max_length=10, default='unknown')
    detected_language = models.CharField(max_length=10, blank=True, null=True)
    asked_count = models.IntegerField(default=1)
    first_asked = models.DateTimeField(auto_now_add=True)
    last_asked = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-asked_count']
    
    def __str__(self):
        return f"{self.question[:50]} ({self.language})"
