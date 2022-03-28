#include "capture.hpp"
#include <iostream>

int main()
{
    for (int i = 0; i < 10000; i++) {
        captureWindowWinRT(853936);
    }
    std::cerr << "Exited normally" << std::endl;
}
