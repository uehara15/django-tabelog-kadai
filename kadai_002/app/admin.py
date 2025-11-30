from django.contrib import admin
from .models import Shop, Category,Company,MemberProfile
from django.utils.safestring import mark_safe

# Register your models here.

class ShopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price','budget','category', 
                    'image','closed_days','opening_hours','detail')
    list_filter = ('category',)


    def image(self, obj):
        if obj.img:
            return mark_safe(f'<img src="{obj.img.url}" style="width:100px; height:auto;">')
        return "(画像なし)"

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded_year', 'headquarters')
    search_fields = ('name', 'headquarters')

# MemberProfile を管理画面に登録
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'birth_date')  # 一覧で表示する項目
    search_fields = ('user__username', 'display_name')    # 検索可能な項目
    list_filter = ('birth_date',)                        # フィルター項目

admin.site.register(Shop,ShopAdmin)
admin.site.register(Category,CategoryAdmin)    
admin.site.register(Company,CompanyAdmin)
admin.site.register(MemberProfile,MemberProfileAdmin)