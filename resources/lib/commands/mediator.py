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
    def sync_cmd(cls, command='undefined', args=None):
        logger.debug('Invoking {}'.format(command))
        if command not in cls._commands:
            logger.warn('Command "{}" not registered'.format(command))
            return
        commands_by_event = cls._commands[command]
        for a_command in commands_by_event:
            try:
                return a_command(args)
            except Exception as ex:
                logger.fatal('Failure processing command "{}"'.format(command), exc_info=ex)
                kodi.notify_error('Failure processing command "{}"'.format(command))
            
    @classmethod
    def async_cmd(cls, command='undefined', args=None):
        kodi.event(command=command, data=args)
