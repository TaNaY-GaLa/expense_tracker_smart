from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # ── Pages ──────────────────────────────────────────────
    path('',           views.home,         name='home'),
    path('history/',   views.history,      name='history'),
    path('split/',     views.split_page,   name='split_page'),
    path('mess/',      views.mess_page,    name='mess_page'),
    path('profile/',   views.profile_page, name='profile_page'),

    # ── Info / About (Task 1) ──────────────────────────────
    path('info/',      views.info_page,    name='info_page'),

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

    # ── Blog (Django template views) ───────────────────────
    path('blog/',                 views.blog_list,   name='blog_list'),
    path('blog/create/',          views.blog_create, name='blog_create'),
    path('blog/<int:id>/',        views.blog_detail, name='blog_detail'),
    path('blog/delete/<int:id>/', views.blog_delete, name='blog_delete'),

    # ════════════════════════════════════════════════════════
    # ── Task 11: DRF Blog REST API ─────────────────────────
    # ════════════════════════════════════════════════════════

    # Auth endpoints
    path('api/v1/auth/register/', api_views.RegisterAPIView.as_view(),  name='drf_register'),
    path('api/v1/auth/login/',    api_views.LoginAPIView.as_view(),     name='drf_login'),
    path('api/v1/auth/logout/',   api_views.LogoutAPIView.as_view(),    name='drf_logout'),

    # Blog post endpoints
    path('api/v1/blog/posts/',               api_views.PostListCreateAPIView.as_view(),           name='drf_post_list'),
    path('api/v1/blog/posts/mine/',          api_views.MyPostsAPIView.as_view(),                  name='drf_my_posts'),
    path('api/v1/blog/posts/<int:id>/',      api_views.PostRetrieveUpdateDestroyAPIView.as_view(), name='drf_post_detail'),
    path('api/v1/blog/posts/<int:id>/similar/', api_views.SimilarPostsAPIView.as_view(),          name='drf_similar_posts'),

    # Stats
    path('api/v1/blog/stats/', api_views.BlogStatsAPIView.as_view(), name='drf_blog_stats'),
]
