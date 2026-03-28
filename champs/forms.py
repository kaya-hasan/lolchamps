from django import forms
from .models import Champion, Review, Role

class ChampionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.order_by("name")

    class Meta:
        model = Champion
        fields = ['name', 'role', 'difficulty', 'playing_freq', 'tier', 'lore', 'is_free']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'playing_freq': forms.Select(attrs={'class': 'form-control'}),
            'tier': forms.Select(attrs={'class': 'form-control'}),
            'lore': forms.Textarea(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect,
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_comment(self):
        comment = self.cleaned_data['comment']
        if len(comment) < 10:
            raise forms.ValidationError('Yorum en az 10 karakter olmalıdır.')
        return comment
      
    def clean_rating(self):
        rating = self.cleaned_data['rating']
        if rating < 1 or rating > 5:
            raise forms.ValidationError('Puan 1 ile 5 arasında olmalıdır.')
        return rating
    
    def clean_difficulty(self):
        difficulty = self.cleaned_data['difficulty']
        if difficulty < 1 or difficulty > 3:
            raise forms.ValidationError('Zorluk 1 ile 3 arasında olmalıdır.')
        return difficulty
    
    def clean_playing_freq(self):
        playing_freq = self.cleaned_data['playing_freq']
        if playing_freq < 1 or playing_freq > 5:
            raise forms.ValidationError('Oynama sıklığı 1 ile 5 arasında olmalıdır.')
        return playing_freq
    
    def clean_tier(self):
        tier = self.cleaned_data['tier']
        if tier < 1 or tier > 5:
            raise forms.ValidationError('Tier 1 ile 5 arasında olmalıdır.')
        return tier
