from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    """店舗のカテゴリー（例：居酒屋、カフェ、レストランなど）。
    将来的にカテゴリーを追加・編集したい場合は別テーブルにしておくと便利。"""
    name = models.CharField("カテゴリ名", max_length=50, unique=True)
    img = models.ImageField(blank=True, default='noImage.png')

    class Meta:
        verbose_name = "カテゴリ"
        verbose_name_plural = "カテゴリ"

    def __str__(self):
        return self.name


class Shop(models.Model):
    """
    お店情報モデル
    フィールド説明（格納形式の例）
    - 定休日 (closed_days): CharField で曜日リストや日付リストを格納します。例: ["月", "火"] または ["2025-12-31"]
    - 予算 (budget): 選択肢（LOW/MEDIUM/HIGH）を用意
    - カテゴリー (category): Categoryモデルへの外部キー
    - 営業時間 (opening_hours): CharField を使い、曜日ごとの開閉時間を格納します。
        例: [{"day": "月", "open": "11:00", "close": "22:00"}, {"day": "火", "closed": true}]
    - 住所 (address): 文字列
    - 店舗名 (name): 文字列
    """
    class Budget(models.TextChoices):
        LOW = "LOW", "〜999円"
        MEDIUM = "MED", "1,000〜2,999円"
        HIGH = "HIGH", "3,000円〜"

    name = models.CharField("店舗名", max_length=200, validators=[MinLengthValidator(1)])
    category = models.ForeignKey(
        Category,
        verbose_name="カテゴリ",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shops",
    )
    img = models.ImageField(blank=True, default='noImage.png')
    address = models.CharField("住所", max_length=300, blank=True)
    budget = models.CharField(
        "予算",
        max_length=4,
        choices=Budget.choices,
        default=Budget.MEDIUM,
    )

    # 定休日・営業時間は柔軟性を優先して CharField を使用
    # Django 3.1+ の場合、models.CharField が利用可能（PostgreSQL 以外でも動作）
    closed_days = models.CharField(
        "定休日",
        max_length=10,
        blank=True,
     )

    opening_hours = models.CharField(
        "営業時間",
        max_length=20,
        blank=True,
        )
    
    detail = models.TextField(blank=True, null=True)

    price = models.IntegerField("予約料金（円）", default=1000)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        verbose_name = "店舗"
        verbose_name_plural = "店舗"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["address"])]

    def __str__(self):
        return self.name
    
class Review(models.Model):
    shop = models.ForeignKey(Shop, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # 新しい順

class Reservation(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField("予約日")
    time = models.TimeField("予約時間")
    num_people = models.PositiveIntegerField("人数")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shop', 'date', 'time', 'user')  # 同一ユーザーが同時刻に二重予約できないようにする

    def __str__(self):
        return f"{self.user.username} - {self.shop.name} ({self.date} {self.time})"

class Company(models.Model):
    name = models.CharField(max_length=100, verbose_name="会社名")
    founded_year = models.IntegerField(verbose_name="創立年")
    description = models.TextField(verbose_name="事業内容")
    headquarters = models.CharField(max_length=200, verbose_name="本社所在地")

    def __str__(self):
        return self.name

#会員情報
class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField("生年月日", null=True, blank=True)
    display_name = models.CharField(max_length=100, verbose_name="名前", blank=True)

     # ← Stripe顧客IDを追加
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.display_name
    
#お気に入り
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'shop')  # 同じ店を複数回お気に入りにできない

    def __str__(self):
        return f"{self.user.username} → {self.shop.name}"
    