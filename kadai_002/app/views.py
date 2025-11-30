import stripe
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import CreateView, UpdateView,DeleteView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.contrib.auth import login, logout

from .models import Shop, Review, Category, Reservation, Company, MemberProfile, Favorite
from .forms import RegisterForm, ReviewForm, ReservationForm, MemberProfileForm

stripe.api_key = settings.STRIPE_SECRET_KEY

# ----------------------------
# Shop関連
# ----------------------------
class ShopListView(ListView):
    model = Shop
    template_name = 'app/shop_list.html'
    context_object_name = 'shops'
    paginate_by = 9  # 1ページあたりの表示件数

    def get_queryset(self):
        queryset = super().get_queryset()
        keyword = self.request.GET.get('keyword', '')
        category_id = self.request.GET.get('category_id', '')

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        return queryset.order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['keyword'] = self.request.GET.get('keyword', '')
        context['selected_category'] = self.request.GET.get('category_id', '')
        return context

class ShopDetailView(TemplateView):
    template_name = 'app/shop_detail.html'

    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        reviews = shop.reviews.all()
        form = ReviewForm()
        return render(request, self.template_name, {
            'shop': shop,
            'reviews': reviews,
            'form': form,
        })

    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        if not request.user.is_authenticated:
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.shop = shop
            review.user = request.user
            review.save()
            return redirect('shop_detail', pk=pk)
        reviews = shop.reviews.all()
        return render(request, self.template_name, {
            'shop': shop,
            'reviews': reviews,
            'form': form,
        })


class ShopUpdateView(LoginRequiredMixin, UpdateView):
    model = Shop
    fields = '__all__'
    template_name_suffix = '_update_form'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('shop_list')
        return super().dispatch(request, *args, **kwargs)

# ----------------------------
# 認証関連
# ----------------------------
class LoginView(TemplateView):
    template_name = 'app/login.html'

    def get(self, request):
            form = AuthenticationForm()
            return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('shop_list')
        return render(request, self.template_name, {'form': form})

def logout_view(request):
    logout(request)
    return redirect('shop_list')

class RegisterView(CreateView):
    template_name = 'app/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

# ----------------------------
# 会社説明ページ
# ----------------------------
class CompanyExplainView(TemplateView):
    template_name = 'app/company_explain.html'

# ----------------------------
# サブスク関連
# ---------------------------
class SubscriptionPageView(TemplateView):
    template_name = 'app/subscription.html'

def create_subscription(request):
    if request.method == "POST":
        session = stripe.checkout.Session.create(
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('cancel')),
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': settings.STRIPE_PRICE_ID,
                'quantity': 1,
            }],
        )
        return redirect(session.url)

    return redirect('/')

# ----------------------------
# 予約関連
# ----------------------------
@login_required
def make_reservation(request, shop_id):
    shop = get_object_or_404(Shop, pk=shop_id)
  
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.shop = shop
            reservation.user = request.user
            reservation.save()
            return redirect('reservation_complete', reservation_id=reservation.id)
   
    else:
        form = ReservationForm(shop=shop)
   
    return render(request, 'app/reservation_form.html', {'form': form, 'shop': shop})

class MyReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'app/my_reservations.html'
    context_object_name = 'reservations'
    paginate_by = 10

    def get_queryset(self):
        # ログインユーザーの予約だけ取得
        return Reservation.objects.filter(user=self.request.user).order_by('-date', '-time')

class ReservationCancelView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'app/reservation_confirm_cancel.html'

    def get_queryset(self):
        # 自分の予約だけ削除可能
        return Reservation.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('my_reservations')


#レビュー
class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Review
    fields = ['content', 'rating']
    template_name = 'app/review_edit.html'

    # 投稿者だけ編集可能
    def test_func(self):
        review = self.get_object()
        return review.user == self.request.user

    def get_success_url(self):
        # 編集後は店舗ページへ戻る
        return reverse_lazy('shop_detail', kwargs={'pk': self.object.shop.pk})


class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'app/review_confirm_delete.html'

    # 投稿者だけ削除可能
    def test_func(self):
        review = self.get_object()
        return review.user == self.request.user

    def get_success_url(self):
        return reverse_lazy('shop_detail', kwargs={'pk': self.object.shop.pk})


@login_required
def reservation_complete(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'app/reservation_complete.html', {'reservation': reservation})

# ----------------------------
# Stripe 決済
# ----------------------------
class CreateCheckoutSessionView(View):
    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'jpy',
                    'product_data': {'name': shop.name},
                    'unit_amount': int(shop.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('cancel')),
        )
        return redirect(checkout_session.url, code=303)

class SuccessPageView(TemplateView):
    template_name = 'app/success.html'

class CancelPageView(TemplateView):
    template_name = 'app/cancel.html'

def company_detail(request):
    company = Company.objects.first()  # 最初の1件を取得
    if not company:
        return render(request, 'app/company_not_found.html')
    return render(request, 'app/company_detail.html', {'company': company})

#stripeの解約
@login_required
def billing_portal(request):
    # MemberProfile がなければ作る（安全策）
    profile, created = MemberProfile.objects.get_or_create(user=request.user)

    # stripe_customer_id カラムが DB に存在するかを try/except で保護
    try:
        customer_id = profile.stripe_customer_id
    except AttributeError:
        # モデル変更後にマイグレーションが実行されていない等の可能性
        messages.error(request, "Stripe 設定が未完了です。管理者に連絡してください。")
        return redirect('member_edit')  # 存在するURL名へ遷移

    # customer_id がなければ Stripe 側で Customer を作成して保存
    if not customer_id:
        try:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=profile.display_name or request.user.get_full_name() or request.user.username,
            )
        except Exception as e:
            # Stripe API エラー時のフォールバック
            messages.error(request, "Stripe API エラー: カスタマーを作成できませんでした。")
            return redirect('member_edit')
        profile.stripe_customer_id = customer.id
        profile.save()
        customer_id = customer.id

    # Billing Portal セッション生成（戻り先は会員編集画面に）
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.build_absolute_uri(reverse("member_edit")),
        )
    except Exception as e:
        messages.error(request, "Stripe ポータルを開けませんでした。管理者に連絡してください。")
        return redirect('member_edit')

    return redirect(session.url)
#会員情報
class MemberProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = MemberProfile
    form_class = MemberProfileForm
    template_name = "app/member_edit.html"

    def get_object(self, queryset=None):
        profile, created = MemberProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse("member_edit")

# ★ お気に入り登録
@login_required
def add_favorite(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    Favorite.objects.get_or_create(user=request.user, shop=shop)
    return redirect('shop_detail', pk=shop_id)


# ★ お気に入り解除
@login_required
def remove_favorite(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    Favorite.objects.filter(user=request.user, shop=shop).delete()
    return redirect('shop_detail', pk=shop_id)


# ★ 自分のお気に入り一覧
@login_required
def my_favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('shop')
    return render(request, "app/my_favorite_list.html", {"favorites": favorites}) 
