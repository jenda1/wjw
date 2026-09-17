import logging

from django.test.runner import DiscoverRunner


class QuietTestRunner(DiscoverRunner):
    """Test runner, který netiskne tracebacky očekávaných 4xx odpovědí.

    Testy záměrně volají pohledy bez potřebných oprávnění nebo na neexistující
    URL. Django takové odpovědi loguje přes logger ``django.request`` jako
    WARNING včetně celého tracebacku, což zaplavuje výstup procházejících testů.
    Logger proto během testů ztišíme na ERROR - chyby 5xx (tedy skutečné
    neočekávané výjimky v pohledech) se logují jako ERROR a vypisují se dál.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        logging.getLogger("django.request").setLevel(logging.ERROR)
