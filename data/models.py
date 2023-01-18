import uuid
from django.db import models

class Category(models.Model):
    px_id = models.IntegerField()
    name = models.CharField(max_length=255)
    ru_name = models.CharField(max_length=255)
    px_slug = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return f'{self.name} / {self.ru_name}'


class Tag(models.Model):
    px_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1025)
    px_slug = models.CharField(max_length=255)
    

    def __str__(self) -> str:
        return f'{self.name}'


class Subcategory(models.Model):
    px_id = models.IntegerField()
    name = models.CharField(max_length=255)
    ru_name = models.CharField(max_length=255)
    category = models.ForeignKey(
        'Category',
        db_column = 'category_id',
        on_delete=models.PROTECT
    )
    faq = models.CharField(max_length=1000, blank=True, null=True)
    px_slug = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "subcategories"
        
    def __str__(self) -> str:
        return f'{self.name} / {self.ru_name}'


class Offer(models.Model):
    PX_SELL = 'sell'
    PX_BUY = 'buy'
    OFFER_TYPE = [
        (PX_SELL, 'Sell'),
        (PX_BUY, 'Buy')
    ]
    BTC = 'BTC'
    USDT = 'USDT'
    CURRENCIES = [
        (BTC, 'Bitcoin'),
        (USDT, 'Tether')
    ]

    px_id = models.CharField(max_length=255)
    sell_cur = models.CharField(
        'cryptoCurrencyCode', max_length=128, choices=CURRENCIES
    )
    buy_cur = models.CharField('fiatCurrencyCode', max_length=128)
    currency = models.ForeignKey(
        'CurrencyDetail',
        db_column = 'currency_ditail_id',
        on_delete=models.PROTECT,
        null=True
    )
    margin = models.FloatField()
    price_per_cur = models.FloatField('pricePerUsd')
    require_verified_id = models.BooleanField()
    tags = models.ManyToManyField('Tag', related_name='offers', blank=True)
    category = models.ForeignKey(
        'Category',
        db_column = 'category_id',
        on_delete=models.PROTECT,
    )
    subcategory = models.ForeignKey(
        'Subcategory',
        db_column = 'subcategory_id',
        on_delete=models.PROTECT
    )
    payment_method_label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    warranty = models.CharField(max_length=255, null=True, blank=True)
    username =  models.CharField(max_length=255)
    score = models.FloatField()
    last_seen = models.CharField('lastSeenString', max_length=255)
    average_trade_speed = models.CharField("releaseTimeMedianHumanize", max_length=255)
    user_timezone = models.CharField(max_length=255)
    offer_type = models.CharField(
        max_length=128, choices=OFFER_TYPE, default=PX_SELL
    )
    offer_detail = models.OneToOneField(
        'OfferDetail',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def offer_info(self):
        margin = self.margin
        predefined_amount = self.offer_detail.predefined_amount
        min = self.offer_detail.fiat_amount_range_min
        max = self.offer_detail.fiat_amount_range_max
        return f'{margin} - {predefined_amount} - {min} - {max}'
    
    def display_amount(self):
        predefined_amount = self.offer_detail.predefined_amount
        min = self.offer_detail.fiat_amount_range_min
        max = self.offer_detail.fiat_amount_range_max
        res = str()
        if predefined_amount != 'null':
            if len(predefined_amount) > 1:
                res += f" {', '.join(str(x) for x in predefined_amount)} {self.buy_cur}."
            else:
                res += f" {predefined_amount[0]} {self.buy_cur}"
        else:
            if min != 'null':
                res += f' min: {min}'
            if max != 'null':
                res += f' | max: {max} {self.buy_cur}.'
        return f'{res}'

    def get_discount(self):
        return round((self.margin-5)/2)

    def __str__(self) -> str:
        name = self.subcategory.name
        margin = self.get_discount()
        res = f'{name}' if len(name) <= 20 else f"{name.replace('Gift Cart', '')}"
        res += self.display_amount()
        return f'-{margin}% {res}'


class OfferDetail(models.Model):
    px_id = models.CharField(max_length=255)
    feedback_negative = models.IntegerField()
    feedback_positive = models.IntegerField()
    predefined_amount = models.JSONField(blank=True)
    fiat_amount_range_min = models.IntegerField()
    fiat_amount_range_max = models.IntegerField()
    fiat_price_per_btc = models.FloatField()
    price_per_btc = models.FloatField()
    fee_percentage = models.IntegerField()
    payment_method_group_id = models.IntegerField()
    percent_per_usd = models.FloatField()
    require_full_name_visibility = models.BooleanField()
    default_flow_type = models.CharField(max_length=255)


class TgUser(models.Model):
    tg_id = models.IntegerField()
    username = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    native_language_code = models.CharField(max_length=2)
    language_code = models.CharField(max_length=2, null=True)
    currency = models.CharField(max_length=3, null=True)
    is_bot = models.BooleanField()
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.username


class GiftOrder(models.Model):
    OPEN = 'Open'
    PENDING = 'Pending'
    PAYMENT_RECEIVED = 'Payment Received'
    COMPLETE = 'Complete'
    STATUS = [
        (OPEN, 'open'),
        (PENDING, 'pending'),
        (PAYMENT_RECEIVED, 'payment received'),
        (COMPLETE, 'complete')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=128, choices=STATUS)
    offer = models.ForeignKey(
        'Offer', 
        db_column='offer_id',
        on_delete=models.SET_NULL,
        null=True
    )
    discount = models.FloatField()
    amount = models.IntegerField(default=0)
    price = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        'TgUser', 
        db_column='tg_user_id',
        on_delete=models.CASCADE
    )
    
    def __str__(self):
        return f"{self.status} / {self.user.username} / {self.offer.subcategory.name}"


class CurrencyDetail(models.Model):
    code = models.CharField(max_length=3, unique=True)
    country = models.CharField(max_length=128, null=True)
    
    def __str__(self):
        return f'{self.code} {self.country}'
    
    
class PaymentMethod(models.Model):
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)


class PaymentAddress(models.Model):
    name = models.CharField(max_length=510)
    address = models.CharField(max_length=255)
    network = models.CharField(max_length=255)
    method = models.ForeignKey(
        'PaymentMethod',
        db_column='payment_method_id',
        on_delete=models.SET_NULL,
        null=True
    )
    is_active = models.BooleanField(default=True)
    