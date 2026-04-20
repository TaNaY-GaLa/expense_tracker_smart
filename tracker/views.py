from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from datetime import date, timedelta
from collections import defaultdict

from .models import UserProfile, Transaction, MessBill, SavingsGoal, Split, RATES


# ── Helpers ────────────────────────────────────────────────────
def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

def json_body(request):
    try:
        return json.loads(request.body)
    except Exception:
        return {}

def api_login_required(view_func):
    """For API views — returns 401 JSON instead of redirect."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Auth Views ─────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        error = 'Invalid username or password.'
    return render(request, 'login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        email    = request.POST.get('email', '').strip()
        mobile   = request.POST.get('mobile', '').strip()

        import re
        if len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email):
            error = 'Invalid email format.'
        elif not re.match(r'^[6-9]\d{9}$', mobile):
            error = 'Mobile must be 10 digits starting with 6-9.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already exists.'
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            UserProfile.objects.create(user=user, mobile=mobile, budget=50000)
            return redirect('login')
    return render(request, 'register.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Page Views ──────────────────────────────────────────────────
@login_required
def home(request):
    return render(request, 'index.html', {'username': request.user.username})

@login_required
def history(request):
    return render(request, 'history.html', {'username': request.user.username})

@login_required
def split_page(request):
    return render(request, 'split.html', {'username': request.user.username})

@login_required
def mess_page(request):
    return render(request, 'mess.html', {'username': request.user.username})

@login_required
def profile_page(request):
    profile = get_or_create_profile(request.user)
    return render(request, 'profile.html', {
        'username': request.user.username,
        'user': request.user,
        'profile': profile,
    })

def info_page(request):
    """Task 1 — Standalone HTML5 About/Info page. Public (no login required)."""
    return render(request, 'info.html')


# ── Transactions API ────────────────────────────────────────────
@csrf_exempt
@api_login_required
def api_transactions(request):
    if request.method == 'GET':
        txns = Transaction.objects.filter(user=request.user)
        data = [{
            'id': t.id, 'title': t.title, 'amount': t.amount,
            'category': t.category, 'date': str(t.date),
            'currency': t.currency, 'amount_inr': t.amount_inr,
        } for t in txns]
        return JsonResponse({'status': 'success', 'count': len(data), 'transactions': data})

    if request.method == 'POST':
        body     = json_body(request)
        title    = body.get('title', '').strip()
        amount   = body.get('amount', 0)
        category = body.get('category', 'Other')
        txn_date = body.get('date', str(date.today()))
        currency = body.get('currency', 'INR')

        if not title:
            return JsonResponse({'error': 'Title cannot be empty'}, status=400)
        if float(amount) <= 0:
            return JsonResponse({'error': 'Amount must be positive'}, status=400)
        if currency not in RATES:
            return JsonResponse({'error': 'Invalid currency'}, status=400)

        txn = Transaction.objects.create(
            user=request.user, title=title, amount=float(amount),
            category=category, date=txn_date, currency=currency
        )
        return JsonResponse({'status': 'success', 'transaction': {
            'id': txn.id, 'title': txn.title, 'amount': txn.amount,
            'category': txn.category, 'date': str(txn.date),
            'currency': txn.currency, 'amount_inr': txn.amount_inr,
        }}, status=201)


@csrf_exempt
@api_login_required
def api_transaction_detail(request, id):
    txn = get_object_or_404(Transaction, id=id, user=request.user)

    if request.method == 'PUT':
        body = json_body(request)
        txn.title    = body.get('title', txn.title).strip()
        txn.amount   = float(body.get('amount', txn.amount))
        txn.category = body.get('category', txn.category)
        txn.date     = body.get('date', str(txn.date))
        txn.currency = body.get('currency', txn.currency)
        txn.save()
        return JsonResponse({'status': 'updated', 'transaction': {
            'id': txn.id, 'title': txn.title, 'amount': txn.amount,
            'category': txn.category, 'date': str(txn.date),
            'currency': txn.currency, 'amount_inr': txn.amount_inr,
        }})

    if request.method == 'DELETE':
        txn.delete()
        return JsonResponse({'status': 'deleted'})


@csrf_exempt
@api_login_required
def api_summary(request):
    txns    = Transaction.objects.filter(user=request.user)
    total   = sum(t.amount_inr for t in txns)
    profile = get_or_create_profile(request.user)
    return JsonResponse({
        'status': 'success',
        'total_expense_inr': round(total, 2),
        'transaction_count': txns.count(),
        'budget': profile.budget,
    })


@csrf_exempt
@api_login_required
def api_budget(request):
    if request.method == 'PUT':
        body   = json_body(request)
        budget = float(body.get('budget', 0))
        if budget <= 0:
            return JsonResponse({'error': 'Budget must be positive'}, status=400)
        profile = get_or_create_profile(request.user)
        profile.budget = budget
        profile.save()
        return JsonResponse({'status': 'budget updated', 'budget': budget})


# ── Analytics API ───────────────────────────────────────────────
@csrf_exempt
@api_login_required
def api_analytics(request):
    txns    = Transaction.objects.filter(user=request.user)
    profile = get_or_create_profile(request.user)

    monthly    = defaultdict(float)
    cat_totals = defaultdict(float)
    dow        = defaultdict(float)
    this_cat   = defaultdict(float)
    last_cat   = defaultdict(float)

    now        = timezone.now()
    this_month = now.strftime('%Y-%m')
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

    for t in txns:
        ym = str(t.date)[:7]
        monthly[ym]            += t.amount_inr
        cat_totals[t.category] += t.amount_inr
        dow[t.date.strftime('%a')] += t.amount_inr
        if ym == this_month: this_cat[t.category] += t.amount_inr
        if ym == last_month: last_cat[t.category] += t.amount_inr

    return JsonResponse({
        'monthly':     dict(sorted(monthly.items())),
        'categories':  dict(sorted(cat_totals.items(), key=lambda x: -x[1])),
        'day_of_week': dict(dow),
        'this_month':  dict(this_cat),
        'last_month':  dict(last_cat),
        'budget':      profile.budget,
        'total':       round(sum(cat_totals.values()), 2),
    })


# ── Profile API ─────────────────────────────────────────────────
@csrf_exempt
@api_login_required
def api_profile(request):
    if request.method == 'PUT':
        body    = json_body(request)
        profile = get_or_create_profile(request.user)
        if 'email'     in body: request.user.email = body['email']; request.user.save()
        if 'mobile'    in body: profile.mobile    = body['mobile']
        if 'language'  in body: profile.language  = body['language']
        if 'dark_mode' in body: profile.dark_mode = body['dark_mode']
        if 'budget'    in body: profile.budget    = float(body['budget'])
        if body.get('password'):
            request.user.set_password(body['password'])
            request.user.save()
        profile.save()
        return JsonResponse({'status': 'updated'})


# ── Savings Goals API ───────────────────────────────────────────
@csrf_exempt
@api_login_required
def api_savings_goals(request):
    if request.method == 'GET':
        goals = SavingsGoal.objects.filter(user=request.user)
        return JsonResponse({'goals': [{
            'id': g.id, 'title': g.title, 'target': g.target,
            'saved': g.saved, 'deadline': str(g.deadline) if g.deadline else '',
            'progress_pct': g.progress_pct,
        } for g in goals]})

    if request.method == 'POST':
        body = json_body(request)
        g = SavingsGoal.objects.create(
            user=request.user,
            title=body.get('title', ''),
            target=float(body.get('target', 0)),
            saved=float(body.get('saved', 0)),
            deadline=body.get('deadline') or None,
        )
        return JsonResponse({'status': 'created', 'goal': {
            'id': g.id, 'title': g.title, 'target': g.target,
            'saved': g.saved, 'deadline': str(g.deadline) if g.deadline else '',
        }}, status=201)


@csrf_exempt
@api_login_required
def api_savings_goal_detail(request, id):
    goal = get_object_or_404(SavingsGoal, id=id, user=request.user)
    if request.method == 'PUT':
        body = json_body(request)
        goal.title    = body.get('title', goal.title)
        goal.target   = float(body.get('target', goal.target))
        goal.saved    = float(body.get('saved', goal.saved))
        goal.deadline = body.get('deadline') or None
        goal.save()
        return JsonResponse({'status': 'updated'})
    if request.method == 'DELETE':
        goal.delete()
        return JsonResponse({'status': 'deleted'})


# ── Mess API ────────────────────────────────────────────────────
@csrf_exempt
@api_login_required
def api_mess(request):
    if request.method == 'GET':
        bills = MessBill.objects.filter(user=request.user)
        return JsonResponse({'bills': [{
            'id': b.id, 'month': b.month, 'amount': b.amount,
            'paid': b.paid, 'note': b.note,
        } for b in bills]})

    if request.method == 'POST':
        body = json_body(request)
        b = MessBill.objects.create(
            user=request.user,
            month=body.get('month', ''),
            amount=float(body.get('amount', 0)),
            paid=body.get('paid', False),
            note=body.get('note', ''),
        )
        return JsonResponse({'status': 'created', 'bill': {
            'id': b.id, 'month': b.month, 'amount': b.amount,
            'paid': b.paid, 'note': b.note,
        }}, status=201)


@csrf_exempt
@api_login_required
def api_mess_detail(request, id):
    bill = get_object_or_404(MessBill, id=id, user=request.user)
    if request.method == 'PUT':
        body = json_body(request)
        bill.month  = body.get('month', bill.month)
        bill.amount = float(body.get('amount', bill.amount))
        bill.paid   = body.get('paid', bill.paid)
        bill.note   = body.get('note', bill.note)
        bill.save()
        return JsonResponse({'status': 'updated', 'bill': {
            'id': bill.id, 'month': bill.month, 'amount': bill.amount,
            'paid': bill.paid, 'note': bill.note,
        }})
    if request.method == 'DELETE':
        bill.delete()
        return JsonResponse({'status': 'deleted'})


# ── Splits API ──────────────────────────────────────────────────
@csrf_exempt
@api_login_required
def api_splits(request):
    if request.method == 'GET':
        splits = Split.objects.filter(user=request.user)
        return JsonResponse({'splits': [{
            'id': s.id, 'title': s.title, 'total': s.total,
            'date': str(s.date), 'paid_by': s.paid_by,
            'friends': s.friends, 'split_type': s.split_type,
            'shares': s.shares, 'settlements': s.settlements,
        } for s in splits]})

    if request.method == 'POST':
        body = json_body(request)
        if not body.get('title') or not body.get('total') or not body.get('friends'):
            return JsonResponse({'error': 'title, total and friends required'}, status=400)
        s = Split.objects.create(
            user=request.user,
            title=body['title'],
            total=float(body['total']),
            date=body.get('date', str(date.today())),
            paid_by=body.get('paid_by', request.user.username),
            friends=body.get('friends', []),
            split_type=body.get('split_type', 'equal'),
            shares=body.get('shares', {}),
            settlements=body.get('settlements', {}),
        )
        return JsonResponse({'status': 'created', 'split': {
            'id': s.id, 'title': s.title, 'total': s.total,
            'date': str(s.date), 'paid_by': s.paid_by,
            'friends': s.friends, 'split_type': s.split_type,
            'shares': s.shares, 'settlements': s.settlements,
        }}, status=201)


@csrf_exempt
@api_login_required
def api_split_detail(request, id):
    split = get_object_or_404(Split, id=id, user=request.user)
    if request.method == 'DELETE':
        split.delete()
        return JsonResponse({'status': 'deleted'})


@csrf_exempt
@api_login_required
def api_split_settle(request, id):
    split  = get_object_or_404(Split, id=id, user=request.user)
    body   = json_body(request)
    person = body.get('person')
    if person and person in split.settlements:
        split.settlements[person]['settled'] = True
        split.save()
    return JsonResponse({'status': 'settled', 'person': person})


@csrf_exempt
@api_login_required
def api_split_settle_all(request, id):
    split = get_object_or_404(Split, id=id, user=request.user)
    for person in split.settlements:
        split.settlements[person]['settled'] = True
    split.save()
    return JsonResponse({'status': 'all settled'})


# ── Blog Views ──────────────────────────────────────────────────
from .models import Post

@login_required
def blog_list(request):
    posts = Post.objects.all()
    return render(request, 'blog_list.html', {'posts': posts})

@login_required
def blog_detail(request, id):
    post = get_object_or_404(Post, id=id)
    return render(request, 'blog_detail.html', {'post': post})

@login_required
def blog_create(request):
    error = None
    if request.method == 'POST':
        title   = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if not title:
            error = 'Title cannot be empty.'
        elif not content:
            error = 'Content cannot be empty.'
        else:
            post = Post.objects.create(title=title, content=content, author=request.user)
            return redirect('blog_detail', id=post.id)
    return render(request, 'blog_create.html', {'error': error})

@login_required
def blog_delete(request, id):
    post = get_object_or_404(Post, id=id, author=request.user)
    post.delete()
    return redirect('blog_list')
