"""Linux address-space limits shared by all benchmark child processes."""
import resource


def limit_memory(memory_mb):
    """Return a child setup callback; benchmark launches children sequentially."""
    def apply():
        size = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (size, size))
    return apply
