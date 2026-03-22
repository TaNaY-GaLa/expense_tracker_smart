from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile     = models.CharField(max_length=10, blank=True)
    budget     = models.FloatField(default=50000)
    language   = models.CharField(max_length=10, default='en')
    dark_mode  = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"


CATEGORY_CHOICES = [
    ('Food', 'Food'),
    ('Travel', 'Travel'),
    ('Clothing', 'Clothing'),
    ('Entertainment', 'Entertainment'),
    ('Books', 'Books'),
    ('Health', 'Health'),
    ('Other', 'Other'),
]

CURRENCY_CHOICES = [
    ('INR', 'INR'), ('USD', 'USD'), ('EUR', 'EUR'),
    ('GBP', 'GBP'), ('JPY', 'JPY'), ('AED', 'AED'), ('SGD', 'SGD'),
]

RATES = {'INR':1,'USD':83.5,'EUR':90.2,'GBP':105.8,'JPY':0.56,'AED':22.7,'SGD':62.1}


class Transaction(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    title      = models.CharField(max_length=200)
    amount     = models.FloatField()
    category   = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    date       = models.DateField()
    currency   = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='INR')
    amount_inr = models.FloatField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.amount_inr = round(self.amount * RATES.get(self.currency, 1), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - ₹{self.amount_inr}"

    class Meta:
        ordering = ['-date', '-created_at']


class MessBill(models.Model):
    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mess_bills')
    month  = models.CharField(max_length=7)   # YYYY-MM
    amount = models.FloatField()
    paid   = models.BooleanField(default=False)
    note   = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.month} - {'Paid' if self.paid else 'Unpaid'}"

    class Meta:
        ordering = ['-month']


class SavingsGoal(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    title    = models.CharField(max_length=200)
    target   = models.FloatField()
    saved    = models.FloatField(default=0)
    deadline = models.DateField(null=True, blank=True)

    @property
    def progress_pct(self):
        return round((self.saved / self.target) * 100, 1) if self.target > 0 else 0

    def __str__(self):
        return f"{self.title} - {self.progress_pct}%"


import json

class Split(models.Model):
    SPLIT_TYPES = [('equal','Equal'),('custom','Custom'),('percent','Percentage')]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='splits')
    title      = models.CharField(max_length=200)
    total      = models.FloatField()
    date       = models.DateField()
    paid_by    = models.CharField(max_length=100)
    friends    = models.JSONField(default=list)
    split_type = models.CharField(max_length=10, choices=SPLIT_TYPES, default='equal')
    shares      = models.JSONField(default=dict)
    settlements = models.JSONField(default=dict)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.total}"

    class Meta:
        ordering = ['-date', '-created_at']


# ── Blog ───────────────────────────────────────────────────────
class Post(models.Model):
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
