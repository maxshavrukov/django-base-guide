from .basket import Basket

def basket(request):
    """
    Контекстный процессор для передачи объекта корзины во все шаблоны.
    """
    return {'basket': Basket(request)}