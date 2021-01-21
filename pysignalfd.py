import os
import ctypes
import typing
import ctypes.util
from typing import List, Optional

SFD_CLOEXEC = 0o2000000
SFD_NONBLOCK = 0o4000


class Sigset(ctypes.Structure):
    '''
    typedef struct {
        unsigned long sig[_NSIG_WORDS];
    } sigset_t;
    '''

    _fields_ = (('sig', ctypes.c_ulong * 2),)

    @classmethod
    def from_signals(cls, sigs: List[int]) -> 'Sigset':
        sigset = cls()
        Syscall.sigemptyset(sigset)
        for sig in sigs:
            sigset.add(sig)
        return sigset

    def add(self, sig: int) -> None:
        Syscall.sigaddset(self, sig)

    def __repr__(self):
        ret = []
        import pdb
        pdb.set_trace()
        for i, bitmask in enumerate(self.sig):
            if bitmask:
                if mask2list and i <= 1:  # 64 bits in the first two int32s
                    numbers = mask2list(bitmask)  # sorted from low to high
                    if i == 1:
                        numbers = [i << 1 for i in numbers]
                    for number in numbers:
                        ret.append(SIGNAMES.get(number, 'SIG%d' % (number,)))
                else:
                    strvalue = binrepr and binrepr(bitmask) or str(bitmask)
                    ret.append('%d: %s' % (i, strvalue))
        return '{%s}' % (', '.join(ret),)


class Syscall:
    libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

    @classmethod
    def signalfd(cls, fd: int, sigset: Sigset, flags: int) -> int:
        '''
        int signalfd(int fd, const sigset_t *mask, int flags)
        '''
        res = cls.libc.signalfd(fd, ctypes.pointer(sigset), flags)
        if res == -1:
            raise RuntimeError(
                'signalfd(2) failed with errno: %d' % ctypes.get_errno()
            )
        return res

    @classmethod
    def sigemptyset(cls, sigset: Sigset):
        '''
        nt sigemptyset(sigset_t *set)
        '''
        res = cls.libc.sigemptyset(ctypes.pointer(sigset))
        if res != 0:
            raise RuntimeError(
                'sigemptyset(3) failed with errno: %d' % ctypes.get_errno()
            )

    @classmethod
    def sigaddset(cls, sigset: Sigset, signum: int) -> None:
        '''
        int sigaddset(sigset_t *set, int signum)
        '''
        res = cls.libc.sigaddset(ctypes.pointer(sigset), signum)
        if res != 0:
            raise RuntimeError(
                'sigaddset(3) failed with errno: %d' % ctypes.get_errno()
            )

    @classmethod
    def sigismember(cls, sigset: Sigset, signum: int) -> bool:
        '''
        int sigismember(const sigset_t *set, int signum)
        '''
        res = cls.libc.sigismember(ctypes.pointer(sigset), signum)
        if res == -1:
            raise RuntimeError(
                'sigismember(3) failed with errno: %d' % ctypes.get_errno()
            )
        return True if res == 1 else False


def signalfd(
    sigs: List[int],
    *,
    NONBLOCK: Optional[bool] = False,
    CLOEXEC: Optional[bool] = False
):
    sigset = Sigset.from_signals(sigs)
    flags = (SFD_NONBLOCK if NONBLOCK else 0) | (SFD_CLOEXEC if CLOEXEC else 0)
    return Syscall.signalfd(-1, sigset, flags)


if __name__ == '__main__':
    import signal
    signal.pthread_sigmask(signal.SIG_BLOCK, [1, 2])
    fd = signalfd([1, 2], NONBLOCK=True, CLOEXEC=True)

    def hand(fd, mask):
        print(os.read(fd, 10000))

    import selectors
    sel = selectors.DefaultSelector()
    sel.register(fd, selectors.EVENT_READ, hand)
    events = sel.select()
    for key, mask in events:
        key.data(key.fileobj, mask)
