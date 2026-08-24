from main.models import Category  # укажи свою модель категорий

def categories(request):
    return {
        'categories': Category.objects.all()
    }