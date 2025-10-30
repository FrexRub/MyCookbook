class ExceptClientError(Exception):
    pass


class ExceptClientResponseError(Exception):
    def __init__(self, original_exception):
        super().__init__(str(original_exception))
        self.original_exception = original_exception

    def __getattr__(self, item):
        return getattr(self.original_exception, item)


class ExceptTimeoutError(Exception):
    pass


class ExceptNormalizeTextError(Exception):
    pass


class ExceptAddChromaError(Exception):
    pass


class ExceptProcessRecipeError(Exception):
    pass
