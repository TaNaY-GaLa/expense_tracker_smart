from django.contrib import admin
from .models import UserProfile, Transaction, MessBill, SavingsGoal, Split


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'mobile', 'budget', 'language']
    search_fields = ['user__username', 'mobile']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ['title', 'user', 'amount_inr', 'category', 'date', 'currency']
    list_filter   = ['category', 'currency', 'date']
    search_fields = ['title', 'user__username']
    date_hierarchy = 'date'


@admin.register(MessBill)
class MessBillAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'amount', 'paid']
    list_filter  = ['paid']


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'target', 'saved', 'deadline']


@admin.register(Split)
class SplitAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'total', 'paid_by', 'date', 'split_type']
    list_filter  = ['split_type']
    search_fields = ['title']


from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ['title', 'author', 'created_at']
    search_fields = ['title', 'content']
    list_filter   = ['author', 'created_at']
