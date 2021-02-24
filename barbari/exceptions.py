class BarbariError(Exception):
    pass


class BarbariUserError(BarbariError):
    pass


class ConfigNotFound(BarbariUserError):
    pass


class InvalidConfiguration(BarbariUserError):
    pass


class BarbariFlatcamError(Exception):
    pass
