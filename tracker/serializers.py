"""
DRF Serializers — Blog API
Handles: Post CRUD, User registration, Token auth
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post


# ── User (read-only, for nesting into Post) ───────────────────
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email']


# ── Post Serializers ──────────────────────────────────────────
class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view (no full content)."""
    author      = AuthorSerializer(read_only=True)
    excerpt     = serializers.SerializerMethodField()
    word_count  = serializers.SerializerMethodField()

    class Meta:
        model  = Post
        fields = ['id', 'title', 'excerpt', 'author', 'word_count', 'created_at', 'updated_at']

    def get_excerpt(self, obj):
        words = obj.content.split()
        return ' '.join(words[:30]) + ('…' if len(words) > 30 else '')

    def get_word_count(self, obj):
        return len(obj.content.split())


class PostDetailSerializer(serializers.ModelSerializer):
    """Full serializer for create / retrieve / update."""
    author      = AuthorSerializer(read_only=True)
    word_count  = serializers.SerializerMethodField()
    is_owner    = serializers.SerializerMethodField()

    class Meta:
        model  = Post
        fields = ['id', 'title', 'content', 'author', 'word_count', 'is_owner', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_word_count(self, obj):
        return len(obj.content.split())

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request is not None and obj.author == request.user


class PostWriteSerializer(serializers.ModelSerializer):
    """Used for POST (create) and PUT/PATCH (update)."""
    class Meta:
        model  = Post
        fields = ['title', 'content']

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Title must be at least 3 characters.')
        if len(value) > 200:
            raise serializers.ValidationError('Title cannot exceed 200 characters.')
        return value

    def validate_content(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('Content must be at least 10 characters.')
        return value


# ── User Registration ─────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6,
                    style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True,
                    style={'input_type': 'password'}, label='Confirm Password')
    mobile    = serializers.CharField(max_length=10, write_only=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'password2', 'mobile']

    def validate_username(self, value):
        import re
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', value):
            raise serializers.ValidationError('3–20 alphanumeric characters or underscores.')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', value):
            raise serializers.ValidationError('Enter a valid email address.')
        return value

    def validate_mobile(self, value):
        import re
        if not re.match(r'^[6-9]\d{9}$', value):
            raise serializers.ValidationError('10-digit Indian mobile starting with 6–9.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        from .models import UserProfile
        mobile    = validated_data.pop('mobile')
        validated_data.pop('password2')
        password  = validated_data.pop('password')
        user      = User.objects.create_user(password=password, **validated_data)
        UserProfile.objects.create(user=user, mobile=mobile)
        return user


# ── Token response helper ─────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    """Returned after login / register — includes token."""
    token = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'token']

    def get_token(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        return token.key
