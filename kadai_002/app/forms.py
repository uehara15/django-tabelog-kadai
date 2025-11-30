from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Review, Reservation, MemberProfile
from django.utils import timezone
import datetime

#登録フォーム
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="氏名（名）", max_length=30, required=True)
    last_name = forms.CharField(label="氏名（姓）", max_length=30, required=True)
    email = forms.EmailField(label="メールアドレス", required=True)

    # MemberProfile 用の追加フィールド
    display_name = forms.CharField(label="表示名", max_length=100, required=False)
    birth_date = forms.DateField(
            label="生年月日",
            required=False,
            widget=forms.DateInput(attrs={'type': 'date'})
        )

    class Meta:
        model = User
        fields = ["last_name", "first_name", "username", "email", "password1", "password2"]
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            MemberProfile.objects.update_or_create(
                user=user,
                defaults={
                    "display_name": self.cleaned_data.get("display_name"),
                    "birth_date": self.cleaned_data.get("birth_date"),
                }
            )
        return user

#レビュー
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={'rows':3, 'placeholder':'レビューを書く'}),
            'rating': forms.NumberInput(attrs={'type':'number', 'min':1, 'max':5}),
        }

#予約フォーム
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['date', 'time', 'num_people']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'num_people': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        # View から shop を受け取る
        self.shop = kwargs.pop("shop", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
       
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")

        if not date or not time:
            return cleaned_data

        # --- 予約日時 (naive) を作成 ---
        reservation_dt = datetime.datetime.combine(date, time)

        # --- aware に変換（DjangoのTIME_ZONEへ）---
        reservation_dt = timezone.make_aware(reservation_dt)

        # --- 現在日時（aware）---
        now = timezone.now()
        
        if reservation_dt <= now:
            raise forms.ValidationError("予約日時は現在より後の時間を指定してください。")

        # ---- ② 店舗営業時間内かチェック ----
        if self.shop:
            # 例: "11:00-22:00" の場合
            if "-" not in self.shop.opening_hours:
                raise forms.ValidationError("店舗の営業時間情報が正しく設定されていません。")

            open_str, close_str = self.shop.opening_hours.split("-")
            open_time = datetime.datetime.strptime(open_str, "%H:%M").time()
            close_time = datetime.datetime.strptime(close_str, "%H:%M").time()

            if not (open_time <= time < close_time):
                raise forms.ValidationError(
                    f"予約時間は営業時間内 ({open_time.strftime('%H:%M')}〜{close_time.strftime('%H:%M')}) で入力してください。"
                )

        return cleaned_data

class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = MemberProfile
        fields = ['display_name', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'})
        }