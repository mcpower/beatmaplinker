import configparser


class ConfigParser(configparser.ConfigParser):
    """A space-aware ConfigParser.

    Wrap quotes around values and spaces will be retained.
    Taken from:
    http://blog.thekondor.net/2011/11/python-make-configparser-aware-of.html
    """
    def __init__(self, **args):
        KEEP_SPACES_KEYWORD = "keep_spaces"

        self.__keep_spaces = args.get(KEEP_SPACES_KEYWORD, True)
        args.pop(KEEP_SPACES_KEYWORD, None)

        configparser.ConfigParser.__init__(self, **args)

    def get(self, section, option):
        value = configparser.ConfigParser.get(self, section, option)
        if self.__keep_spaces:
            value = self._unwrap_quotes(value)

        return value

    def set(self, section, option, value):
        if self.__keep_spaces:
            value = self._wrap_to_quotes(value)

        configparser.ConfigParser.set(self, section, option, value)

    @staticmethod
    def _unwrap_quotes(src):
        QUOTE_SYMBOLS = ('"', "'")
        for quote in QUOTE_SYMBOLS:
            if src.startswith(quote) and src.endswith(quote):
                return src.strip(quote)

        return src

    @staticmethod
    def _wrap_to_quotes(src):
        if src and src[0].isspace():
            return '"%s"' % src

        return src
