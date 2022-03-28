#pragma once
#include <vector>
typedef uint8_t byte;
struct Size
{
    int width;
    int height;
};

struct CaptureWindowOutput
{
    ::Size size;
    std::vector<byte> frame;
};

CaptureWindowOutput captureWindowBitBlt(uint64_t window);
CaptureWindowOutput captureWindowWinRT(uint64_t window);
