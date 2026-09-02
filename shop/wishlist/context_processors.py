from .services.wishlist import Wishlist


def wishlist(request):
    """Делает объект Wishlist доступным во всех HTML-шаблонах."""
    return {'wishlist': Wishlist(request)}