import os
import struct
import ctypes
import typing
import ctypes.util
from typing import List, Optional, Generator

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


class Syscall:
    libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

    @classmethod
    def signalfd(cls, fd: int, sigset: Sigset, flags: int) -> int:
        '''
        int signalfd(int fd, const sigset_t *mask, int flags)
        '''
        res = cls.libc.signalfd(fd, ctypes.pointer(sigset), flags)
        if res == -1:
            raise OSError(
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
            raise OSError(
                'sigemptyset(3) failed with errno: %d' % ctypes.get_errno()
            )

    @classmethod
    def sigaddset(cls, sigset: Sigset, signum: int) -> None:
        '''
        int sigaddset(sigset_t *set, int signum)
        '''
        res = cls.libc.sigaddset(ctypes.pointer(sigset), signum)
        if res != 0:
            raise OSError(
                'sigaddset(3) failed with errno: %d' % ctypes.get_errno()
            )

    @classmethod
    def sigismember(cls, sigset: Sigset, signum: int) -> bool:
        '''
        int sigismember(const sigset_t *set, int signum)
        '''
        res = cls.libc.sigismember(ctypes.pointer(sigset), signum)
        if res == -1:
            raise OSError(
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


def parse_siginfo(fd: int) -> Generator[int, None, None]:
    '''
    struct signalfd_siginfo {
        uint32_t ssi_signo;    /* Signal number */
        int32_t  ssi_errno;    /* Error number (unused) */
        int32_t  ssi_code;     /* Signal code */
        uint32_t ssi_pid;      /* PID of sender */
        uint32_t ssi_uid;      /* Real UID of sender */
        int32_t  ssi_fd;       /* File descriptor (SIGIO) */
        uint32_t ssi_tid;      /* Kernel timer ID (POSIX timers)
        uint32_t ssi_band;     /* Band event (SIGIO) */
        uint32_t ssi_overrun;  /* POSIX timer overrun count */
        uint32_t ssi_trapno;   /* Trap number that caused signal */
        int32_t  ssi_status;   /* Exit status or signal (SIGCHLD) */
        int32_t  ssi_int;      /* Integer sent by sigqueue(3) */
        uint64_t ssi_ptr;      /* Pointer sent by sigqueue(3) */
        uint64_t ssi_utime;    /* User CPU time consumed (SIGCHLD) */
        uint64_t ssi_stime;    /* System CPU time consumed
                                  (SIGCHLD) */
        uint64_t ssi_addr;     /* Address that generated signal
                                  (for hardware-generated signals) */
        uint16_t ssi_addr_lsb; /* Least significant bit of address
                                  (SIGBUS; since Linux 2.6.37)
        uint8_t  pad[X];       /* Pad size to 128 bytes (allow for
                                  additional fields in the future) */
    };
    '''
    while True:
        try:
            buf = os.read(fd, 128)  # magic number, don't ask
        except BlockingIOError:
            return
        signum, *_ = struct.unpack('I', buf[:4])
        yield signum


if __name__ == '__main__':
    import signal
    signal.pthread_sigmask(signal.SIG_BLOCK, [1, 2])
    fd = signalfd([1, 2], NONBLOCK=True, CLOEXEC=True)

    def hand(fd, mask):
        import time
        time.sleep(10)
        for signum in parse_siginfo(fd):
            print(signum)

    import selectors
    sel = selectors.DefaultSelector()
    sel.register(fd, selectors.EVENT_READ, hand)
    events = sel.select()
    for key, mask in events:
        key.data(key.fileobj, mask)
