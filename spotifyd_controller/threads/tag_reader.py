__all__ = (
    'TagReader',
    'TagReaderActor',
)

from threading import Event, Thread
from time import time
from pykka import ThreadingActor

from pirc522 import RFID

from spotifyd_controller.registry import LOGGER, REGISTRY
from spotifyd_controller.actions.base import Action
from spotifyd_controller.sound import play_sound


class ReadError(Exception):
    '''
    Exception which is thrown when an RFID read error occurs.
    '''


class TagReader(Thread):
    '''
    Thread which reads RFID tags from the RFID reader.
    Because the RFID reader algorithm is reacting to an IRQ (interrupt), it is
    blocking as long as no tag is touched, even when Mopidy is exiting. Thus,
    we're running the thread as daemon thread, which means it's exiting at the
    same moment as the main thread (aka Mopidy core) is exiting.
    '''
    daemon = True
    latest = None

    def __init__(self, player, stop_event):
        '''
        Class constructor.
        :param mopidy.core.Core core: The mopidy core instance
        :param threading.Event stop_event: The stop event
        '''
        super().__init__()
        self.player = player
        self.stop_event = stop_event
        self.rfid = RFID()

    def run(self):
        '''
        Run RFID reading loop.
        '''
        rfid = self.rfid
        prev_time = time()
        prev_uid = ''

        print('tag reader start')

        while not self.stop_event.is_set():
            rfid.wait_for_tag()

            try:
                now = time()
                uid = self.read_uid()

                if now - prev_time > 1 or uid != prev_uid:
                    print('Tag %s read', uid)
                    self.handle_uid(uid)

                prev_time = now
                prev_uid = uid

            except ReadError:
                pass

        rfid.cleanup()  # pylint: disable=no-member

    def read_uid(self):
        '''
        Return the UID from the tag.
        :return: The hex UID
        :rtype: string
        '''
        rfid = self.rfid

        error, data = rfid.request()  # pylint: disable=unused-variable
        if error:
            raise ReadError('Could not read tag')

        error, uid_chunks = rfid.anticoll()
        if error:
            raise ReadError('Could not read UID')

        uid = '{0[0]:02X}{0[1]:02X}{0[2]:02X}{0[3]:02X}'.format(
            uid_chunks)  # pylint: disable=invalid-format-index
        return uid

    def handle_uid(self, uid):
        '''
        Handle the scanned tag / retreived UID.
        :param str uid: The UID
        '''
        try:
            action = REGISTRY[str(uid)]
            print('Triggering action of registered tag')
            play_sound('success.wav')
            action(self.player)

        except KeyError:
            print('Tag is not registered, thus doing nothing')
            play_sound('fail.wav')
            action = Action(uid=uid)

        action.scanned = time()
        TagReader.latest = action


class TagReaderActor(ThreadingActor):
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
        self.tag_reader = TagReader(self.stop_event)

    def on_receive(self, message):
        if (message == 'latest'):
            return self.tag_reader.latest

    def on_start(self):
        '''
        Start tag reader thread.
        '''
        LOGGER.info('start sensor')
        self.tag_reader.start()

    def on_stop(self):
        '''
        Set threading stop event to tell tag reader thread to
        stop its operations.
        '''
        LOGGER.info('stop sensor')
        self.stop_event.set()
