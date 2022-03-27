#include "semaphore.hpp"
semaphore::semaphore(unsigned long count) : count_(count) {}

void semaphore::release()
{
    std::lock_guard<decltype(mutex_)> lock(mutex_);
    ++count_;
    condition_.notify_one();
}

void semaphore::acquire()
{
    std::unique_lock<decltype(mutex_)> lock(mutex_);
    while (!count_) // Handle spurious wake-ups.
        condition_.wait(lock);
    --count_;
}

bool semaphore::try_acquire()
{
    std::lock_guard<decltype(mutex_)> lock(mutex_);
    if (count_)
    {
        --count_;
        return true;
    }
    return false;
}
