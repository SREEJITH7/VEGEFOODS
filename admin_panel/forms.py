from django import forms
from .models import Catogery, Product, ProductImage

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Catogery
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name',
                'id': 'categoryName'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category description',
                'id': 'categoryDescription',
                'rows': 3
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name.isalpha():
            raise forms.ValidationError("Category name should only contain alphabets.")
        return name


# _______________ adding product form __________________________

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'base_price', 'stock_quantity', 'catogery','discount_percentage', 'offer_price']  




























