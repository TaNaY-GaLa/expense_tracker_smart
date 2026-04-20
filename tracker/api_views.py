"""
DRF Blog API Views
==================
Endpoints:
  POST   /api/v1/auth/register/        — Register a new user, returns token
  POST   /api/v1/auth/login/           — Login, returns token
  POST   /api/v1/auth/logout/          — Invalidate token

  GET    /api/v1/blog/posts/           — List all posts (paginated, searchable)
  POST   /api/v1/blog/posts/           — Create a post (auth required)
  GET    /api/v1/blog/posts/<id>/      — Retrieve a single post
  PUT    /api/v1/blog/posts/<id>/      — Full update (author only)
  PATCH  /api/v1/blog/posts/<id>/      — Partial update (author only)
  DELETE /api/v1/blog/posts/<id>/      — Delete (author only)

  GET    /api/v1/blog/posts/mine/      — My posts only
  GET    /api/v1/blog/posts/<id>/similar/ — Posts by same author
"""
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
)
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .models import Post
from .serializers import (
    PostListSerializer, PostDetailSerializer,
    PostWriteSerializer, RegisterSerializer, UserProfileSerializer
)


# ── Custom Permissions ────────────────────────────────────────
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    """Only the post's author can edit or delete it; everyone can read."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


# ── Auth Views ────────────────────────────────────────────────

class RegisterAPIView(APIView):
    """
    POST /api/v1/auth/register/
    Register a new user. Returns auth token on success.
    Body: { username, email, password, password2, mobile }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status':  'success',
                'message': 'Account created successfully.',
                'user':    UserProfileSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 'error',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """
    POST /api/v1/auth/login/
    Login with username + password. Returns auth token.
    Body: { username, password }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'status': 'error', 'message': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if user:
            return Response({
                'status':  'success',
                'message': f'Welcome back, {user.username}!',
                'user':    UserProfileSerializer(user).data,
            }, status=status.HTTP_200_OK)

        return Response(
            {'status': 'error', 'message': 'Invalid username or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutAPIView(APIView):
    """
    POST /api/v1/auth/logout/
    Invalidate the current auth token.
    Requires: Token authentication header.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response(
            {'status': 'success', 'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK
        )


# ── Blog Post Views ───────────────────────────────────────────

class PostListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/v1/blog/posts/   — List all posts (paginated)
    POST /api/v1/blog/posts/   — Create a new post (auth required)

    Query params:
      ?search=<term>    — search in title and content
      ?ordering=<field> — order by created_at, title, -created_at
      ?page=<n>         — page number (10 per page)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes     = [IsAuthenticatedOrReadOnly]
    filter_backends        = [filters.SearchFilter, filters.OrderingFilter]
    search_fields          = ['title', 'content', 'author__username']
    ordering_fields        = ['created_at', 'updated_at', 'title']
    ordering               = ['-created_at']

    def get_queryset(self):
        return Post.objects.select_related('author').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostWriteSerializer
        return PostListSerializer

    def create(self, request, *args, **kwargs):
        serializer = PostWriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save(author=request.user)
            return Response({
                'status':  'success',
                'message': 'Post created successfully.',
                'post':    PostDetailSerializer(post, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 'error',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset   = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(queryset)
        serializer = PostListSerializer(page, many=True, context={'request': request})
        paginated  = self.get_paginated_response(serializer.data)
        paginated.data['status'] = 'success'
        return paginated


class PostRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/blog/posts/<id>/  — Retrieve a post
    PUT    /api/v1/blog/posts/<id>/  — Full update (author only)
    PATCH  /api/v1/blog/posts/<id>/  — Partial update (author only)
    DELETE /api/v1/blog/posts/<id>/  — Delete (author only)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes     = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    queryset               = Post.objects.select_related('author').all()
    lookup_field           = 'id'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PostWriteSerializer
        return PostDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        return Response({
            'status': 'success',
            'post':   PostDetailSerializer(post, context={'request': request}).data,
        })

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop('partial', False)
        post       = self.get_object()
        serializer = PostWriteSerializer(post, data=request.data,
                                         partial=partial, context={'request': request})
        if serializer.is_valid():
            updated = serializer.save()
            return Response({
                'status':  'success',
                'message': 'Post updated successfully.',
                'post':    PostDetailSerializer(updated, context={'request': request}).data,
            })
        return Response({
            'status': 'error',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        title = post.title
        post.delete()
        return Response({
            'status':  'success',
            'message': f'Post "{title}" deleted successfully.',
        }, status=status.HTTP_200_OK)


class MyPostsAPIView(generics.ListAPIView):
    """
    GET /api/v1/blog/posts/mine/
    Returns only the authenticated user's posts (paginated).
    Requires auth token.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes     = [IsAuthenticated]
    serializer_class       = PostListSerializer
    filter_backends        = [filters.SearchFilter, filters.OrderingFilter]
    search_fields          = ['title', 'content']
    ordering_fields        = ['created_at', 'title']
    ordering               = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).select_related('author')

    def list(self, request, *args, **kwargs):
        queryset   = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(queryset)
        serializer = PostListSerializer(page, many=True, context={'request': request})
        paginated  = self.get_paginated_response(serializer.data)
        paginated.data['status'] = 'success'
        paginated.data['author'] = request.user.username
        return paginated


class SimilarPostsAPIView(APIView):
    """
    GET /api/v1/blog/posts/<id>/similar/
    Returns up to 5 other posts by the same author.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes     = [AllowAny]

    def get(self, request, id):
        post    = get_object_or_404(Post, id=id)
        similar = Post.objects.filter(author=post.author).exclude(id=id).order_by('-created_at')[:5]
        return Response({
            'status':      'success',
            'post_id':     id,
            'author':      post.author.username,
            'similar_count': similar.count(),
            'posts':       PostListSerializer(similar, many=True, context={'request': request}).data,
        })


class BlogStatsAPIView(APIView):
    """
    GET /api/v1/blog/stats/
    Returns aggregate statistics about the blog.
    Public endpoint — no auth needed.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.models import Count
        total_posts   = Post.objects.count()
        total_authors = Post.objects.values('author').distinct().count()
        top_authors   = (
            User.objects.annotate(post_count=Count('posts'))
            .filter(post_count__gt=0)
            .order_by('-post_count')[:5]
            .values('username', 'post_count')
        )
        recent = Post.objects.select_related('author').order_by('-created_at')[:5]

        return Response({
            'status':        'success',
            'total_posts':   total_posts,
            'total_authors': total_authors,
            'top_authors':   list(top_authors),
            'recent_posts':  PostListSerializer(recent, many=True, context={'request': request}).data,
        })
