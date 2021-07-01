import logging

from ael.utils import text, kodi

logger = logging.getLogger(__name__)

class AppMediator(object):

    _commands = {}

    @classmethod
    def register(cls, event: str):
        def decorator(func):
            logger.debug('Registering event "{}"'.format(event))
            cls.register_command(event, func)
            return func
        return decorator

    @classmethod
    def register_command(cls, event, command):
        if event not in cls._commands:
            cls._commands[event] = []
        cls._commands[event].append(command)

    @classmethod
    def invoke(cls, event, args):
        logger.debug('Invoking {}'.format(event))
        if event not in cls._commands:
            logger.warn('Command "{}" not registered'.format(event))
            return
        commands_by_event = cls._commands[event]
        for command in commands_by_event:
            try:
                command(args)
            except Exception as ex:
                message = text.createError(ex)
                logger.fatal(message)
                kodi.notify_error('Failure processing command "{}"'.format(event))
