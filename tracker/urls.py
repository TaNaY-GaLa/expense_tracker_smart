from django.urls import path
from . import views

urlpatterns = [
    # ── Pages ──────────────────────────────────────────────
    path('',           views.home,         name='home'),
    path('history/',   views.history,      name='history'),
    path('split/',     views.split_page,   name='split_page'),
    path('mess/',      views.mess_page,    name='mess_page'),
    path('profile/',   views.profile_page, name='profile_page'),

    # ── Auth ───────────────────────────────────────────────
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),

    # ── Transactions API ───────────────────────────────────
    path('api/transactions/',         views.api_transactions,       name='api_transactions'),
    path('api/transactions/<int:id>/', views.api_transaction_detail, name='api_transaction_detail'),
    path('api/summary/',              views.api_summary,            name='api_summary'),
    path('api/budget/',               views.api_budget,             name='api_budget'),
    path('api/analytics/',            views.api_analytics,          name='api_analytics'),

    # ── Profile API ────────────────────────────────────────
    path('api/profile/', views.api_profile, name='api_profile'),

    # ── Savings Goals API ──────────────────────────────────
    path('api/savings-goals/',         views.api_savings_goals,      name='api_savings_goals'),
    path('api/savings-goals/<int:id>/', views.api_savings_goal_detail, name='api_savings_goal_detail'),

    # ── Mess API ───────────────────────────────────────────
    path('api/mess/',         views.api_mess,        name='api_mess'),
    path('api/mess/<int:id>/', views.api_mess_detail, name='api_mess_detail'),

    # ── Splits API ─────────────────────────────────────────
    path('api/splits/',                    views.api_splits,           name='api_splits'),
    path('api/splits/<int:id>/',           views.api_split_detail,     name='api_split_detail'),
    path('api/splits/<int:id>/settle/',    views.api_split_settle,     name='api_split_settle'),
    path('api/splits/<int:id>/settle-all/', views.api_split_settle_all, name='api_split_settle_all'),

    # ── Blog ────────────────────────────────────────────────
    path('blog/',                 views.blog_list,   name='blog_list'),
    path('blog/create/',          views.blog_create, name='blog_create'),
    path('blog/<int:id>/',        views.blog_detail, name='blog_detail'),
    path('blog/edit/<int:id>/',   views.blog_edit,   name='blog_edit'),
    path('blog/delete/<int:id>/', views.blog_delete, name='blog_delete'),

    # ── DRF API ─────────────────────────────────────────────
    path('drf/transactions/',          views.drf_transactions,       name='drf_transactions'),
    path('drf/transactions/<int:id>/', views.drf_transaction_detail, name='drf_transaction_detail'),
    path('drf/blog/',                  views.drf_blog_list,          name='drf_blog_list'),
    path('drf/blog/<int:id>/',         views.drf_blog_detail,        name='drf_blog_detail'),
]
